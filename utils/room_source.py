"""
A dialog room as a816 source over src/room_macros.s: every opcode the disassembler walked becomes its macro call, every
header or table word a `.dw`, every text and every byte the walk did not reach a `.db`. Assembled, the source gives
the room back byte for byte: the round trip checks the macros' layouts against the opcode lengths the walk read.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from a816.module_builder import build_with_imports

from utils.vm.opcodes import ActorList, Opcode13
from utils.vm.opcodes_map import opcode_table
from utils.vm.program import Entry
from utils.vm.room import Room

MACROS = Path("src/room_macros.s")
MACRO_NAME = re.compile(r"^\.macro (?P<name>\w+)\(")
DATA_LINE = re.compile(r"^\s+\.(?P<kind>db|dw) (?P<values>.+)$")
# Opcodes whose operands end in a list closed by FF (or FE): the macro writes the head, the list follows as `.db`.
LIST_OPCODES = frozenset(
    opcode for opcode, handler in opcode_table.items() if isinstance(handler, Opcode13 | ActorList)
)
NO_MACRO = "no macro fits"  # an opcode written raw: its macro's layout disagrees with the length the walk read
HEADER = [
    f'.include "{MACROS}"',
    "",
    "*= 0x008000  ; file offset 0 of a LoROM image",
    "@= 0x7F0000  ; WRAM, where rooms run: a word keeps the room offset the VM reads",
    "",
]


@dataclass(frozen=True)
class Macro:
    """A room macro: its name and the width of each parameter, in the order its body emits them."""

    name: str
    widths: tuple[int, ...]

    @property
    def size(self) -> int:
        return 1 + sum(self.widths)


def read_macros(source: str) -> dict[int, Macro]:
    """The macros of src/room_macros.s by opcode: the opcode is the body's first `.db` value."""
    macros: dict[int, Macro] = {}
    name: str | None = None
    opcode: int | None = None
    widths: list[int] = []
    for line in source.splitlines():
        start = MACRO_NAME.match(line)
        if start:
            name, opcode, widths = start["name"], None, []
            continue
        if name is None:
            continue
        if line == "}":
            if opcode is not None:
                macros[opcode] = Macro(name, tuple(widths))
            name = None
            continue
        data = DATA_LINE.match(line)
        if data:
            values = [value.strip() for value in data["values"].split(",")]
            if opcode is None:
                opcode = int(values.pop(0), 16)
            widths += [1 if data["kind"] == "db" else 2] * len(values)
    return macros


def label(address: int) -> str:
    return f"room_{address:04x}"


def bytes_line(data: bytes, note: str = "") -> str:
    line = "    .db " + ", ".join(f"0x{byte:02X}" for byte in data)
    return f"{line}  ; {note}" if note else line


class RoomSource:
    """Writes one walked room as a816 source."""

    def __init__(self, room: Room, macros: dict[int, Macro]) -> None:
        self.data = room.data
        self.macros = macros
        self.listing = room.program.filter(lambda _address, _entry: True)
        self.starts = sorted(address for address in self.listing if address < len(self.data))
        self.targets = set(self.starts)

    def operand(self, value: int, width: int) -> str:
        """A word that lands on a walked entry is that entry's label: the source then survives moving code."""
        if width == 2 and value in self.targets:
            return label(value)
        return f"0x{value:0{width * 2}X}"

    def macro_lines(self, data: bytes, note: str) -> list[str] | None:
        """An opcode as its macro call (and its list, for a list opcode), or None when no macro fits its bytes."""
        macro = self.macros.get(data[0])
        if macro is None or not (macro.size == len(data) or macro.size < len(data) and data[0] in LIST_OPCODES):
            return None
        operands = []
        offset = 1
        for width in macro.widths:
            operands.append(self.operand(int.from_bytes(data[offset : offset + width], "little"), width))
            offset += width
        lines = [f"    {macro.name}({', '.join(operands)})" + (f"  ; {note}" if note else "")]
        if offset < len(data):
            lines.append(bytes_line(data[offset:]))
        return lines

    def entry_lines(self, address: int, entry: Entry, end: int) -> tuple[list[str], int]:
        """The entry's source and the address after it. Text that runs into another entry (strings sharing a tail)
        stops at that entry's label; anything else that does not fit is written raw, with the reason."""
        element, comment, size = entry
        note = (comment or "").replace("\n", " ")
        if element[0] == "text" and address + size > end:
            return [bytes_line(self.data[address:end], note)], end
        if address + size > end:
            reason = "runs past the room's end" if end == len(self.data) else f"overlaps the entry at 0x{end:04X}"
            return [bytes_line(self.data[address:end], reason)], end
        data = self.data[address : address + size]
        if element[0] == "reference" and size == 2:
            word = self.operand(int.from_bytes(data, "little"), 2)
            return [f"    .dw {word}" + (f"  ; {note}" if note else "")], address + size
        if element[0] == "opcode":
            lines = self.macro_lines(data, note)
            if lines is None:
                return [bytes_line(data, f"{NO_MACRO}: opcode 0x{data[0]:02X}, {size} bytes")], address + size
            return lines, address + size
        return [bytes_line(data, note)], address + size

    def lines(self) -> list[str]:
        out = list(HEADER)
        address = 0
        while address < len(self.data):
            end = next((start for start in self.starts if start > address), len(self.data))
            if address in self.targets:
                out.append(f"{label(address)}:")
            entry = self.listing.get(address)
            if entry is None:
                out.append(bytes_line(self.data[address:end], "not walked"))
                address = end
                continue
            lines, address = self.entry_lines(address, entry, end)
            out += lines
        return out


def room_source(room: Room, macros: dict[int, Macro]) -> str:
    return "\n".join(RoomSource(room, macros).lines()) + "\n"


def assemble_room(source: Path, output: Path, obj_dir: Path) -> list[str]:
    """Assemble a room source to raw bytes in output: a816's diagnostics, empty on success. The project's a816.toml
    (HiROM, the patch's modules) stays out: a room is a plain image from offset 0."""
    result = build_with_imports(
        main_source=source,
        output_file=output,
        output_format="sfc",
        output_dir=obj_dir,
        include_paths=[Path.cwd()],
        use_a816_toml=False,
        use_cache=False,
    )
    if result.exit_code != 0:
        return result.diagnostics or [f"a816 failed on {source}"]
    return []
