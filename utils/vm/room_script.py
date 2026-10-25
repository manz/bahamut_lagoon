"""Disassemble a dialog room: its header entries, then the room from start to end as named instructions (the code
utils.vm.room_walk reaches) and data (the header and its tables, texts, palettes, bytes nothing reaches).

Jump and call targets and entry points get an `L` label, texts a `T` one, palette data a `D` one; a text operand
shows the text. --fr reads the French build (build/bl.ips over build/bl.sfc), the Japanese ROM otherwise.

    uv run python -m utils.vm.room_script 13 [--fr] [--bytes]
"""

import argparse
import tempfile
from bisect import bisect_right
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

from katsuji.script import Table

from utils.cartridge import rom_offset
from utils.credits import CREDITS_ROOMS, ENDING_CREDITS_ROOMS
from utils.credits import TABLE as CREDITS_TABLE
from utils.dump_rooms import is_compressed
from utils.ips import apply_ips
from utils.vm.opcodes import bl_prefix_lookup_chars
from utils.vm.room_ops import OPERANDS, Instruction
from utils.vm.room_walk import ROOM_POINTERS, ROOMS, Walk, room_data, text_length, walk_room

ROM = Path("build/bl.sfc")
IPS = Path("build/bl.ips")
JP_TABLE = Path("text/table/jp.tbl")
FR_TABLE = Path("text/table/mz.tbl")
ROW = 16  # bytes per db line


@dataclass(frozen=True)
class Data:
    """Room bytes that are not code: `kind` is text, data (the header, its tables and records, palettes) or
    unreached."""

    offset: int
    raw: bytes
    kind: str


Item = Instruction | Data


def _cuts(walk: Walk, lo: int, hi: int) -> list[int]:
    """Where the bytes [lo, hi) between two instructions change meaning: each covered range's start and end."""
    cuts = {lo, hi}
    for start, length in walk.covered.items():
        cuts |= {c for c in (start, start + length) if lo < c < hi}
    return sorted(cuts)


def _data(walk: Walk, lo: int, hi: int, texts: set[int]) -> list[Data]:
    cuts = _cuts(walk, lo, hi)
    items = []
    for start, end in pairwise(cuts):
        reached = any(o <= start < o + n for o, n in walk.covered.items())
        kind = "text" if start in texts else "data" if reached else "unreached"
        items.append(Data(start, walk.data[start:end], kind))
    return items


def disassemble(walk: Walk) -> list[Item]:
    """The room's bytes in order, each in exactly one item: reached instructions, and the data between them."""
    texts = {t for ins in walk.code.values() for t in ins.texts}
    starts = sorted(walk.code)
    items: list[Item] = []
    at = 0
    while at < len(walk.data):
        if at in walk.code:
            items.append(walk.code[at])
            at += walk.code[at].size
            continue
        later = bisect_right(starts, at)
        end = starts[later] if later < len(starts) else len(walk.data)
        items += _data(walk, at, end, texts)
        at = end
    return items


def rom_image(fr: bool) -> bytes:
    rom = ROM.read_bytes()
    return apply_ips(rom, IPS.read_bytes()) if fr else rom


def _pointer(rom: bytes, room: int) -> int:
    at = rom_offset(ROOM_POINTERS) + 3 * room
    return int.from_bytes(rom[at : at + 3], "little")


def raw_room(rom: bytes, room: int) -> bytes:
    """A room the build stored raw (too big once decompressed): up to the next room's start."""
    start = _pointer(rom, room)
    end = min((p for p in (_pointer(rom, r) for r in range(ROOMS)) if p > start), default=start)
    return rom[rom_offset(start) : rom_offset(end)]


def load_room(room: int, fr: bool) -> bytes:
    with open(ROM, "rb") as vanilla:
        if not is_compressed(vanilla, room):
            raise SystemExit(f"room {room} has no script (stored raw in the Japanese ROM)")
    rom = rom_image(fr)
    with tempfile.TemporaryDirectory() as scratch:  # the room readers take a file
        image = Path(scratch) / "bl.sfc"
        image.write_bytes(rom)
        with open(image, "rb") as reader:
            data = room_data(reader, room)
    return raw_room(rom, room) if data is None else data


def text_decoder(room: int, fr: bool) -> Callable[[bytes], str]:
    credits = room in CREDITS_ROOMS | ENDING_CREDITS_ROOMS
    table = Table(str(CREDITS_TABLE if credits else FR_TABLE if fr else JP_TABLE))
    prefixed = bl_prefix_lookup_chars if not fr else bytes
    return lambda raw: quote(table.to_text(prefixed(raw)))


def quote(text: str) -> str:
    """A text on one line: the table's spaces (`\\s`) as spaces, line breaks as `\\n`."""
    return '"' + text.replace("\\s", " ").replace("\n", "\\n") + '"'


def _operand(kind: str, value: int | bytes, texts: Callable[[int], str]) -> tuple[str, str]:
    """The operand as shown, and a note for the line (a text's content)."""
    if isinstance(value, bytes):
        return f"[{value.hex(' ')}]", ""
    if kind == "j":
        return f"L{value:04x}", ""
    if kind == "t":
        return f"T{value:04x}", texts(value)
    if kind == "p":
        return f"D{value:04x}", ""
    width = {"b": 2, "w": 4, "a": 6}[kind]
    return f"0x{value:0{width}x}", ""


def _instruction(ins: Instruction, texts: Callable[[int], str]) -> tuple[str, list[str]]:
    shown = [_operand(k, v, texts) for k, v in zip(OPERANDS[ins.opcode], ins.operands, strict=True)]
    return f"{ins.name} {', '.join(s for s, _ in shown)}".rstrip(), [n for _, n in shown if n]


def _raw(data: bytes, offset: int, size: int, show: bool) -> str:
    return f" {data[offset : offset + size].hex(' '):<24}" if show else ""


def _label(offset: int, labels: dict[int, str], notes: dict[int, list[str]]) -> list[str]:
    if offset not in labels:
        return []
    note = f"  ; {', '.join(notes[offset])}" if notes.get(offset) else ""
    return ["", f"{labels[offset]}:{note}"]


def _data_lines(item: Data, decode: Callable[[bytes], str]) -> list[str]:
    if item.kind == "text":
        return [f"  {item.offset:04x}  text {decode(item.raw)}"]
    lines = []
    for at in range(0, len(item.raw), ROW):
        row = item.raw[at : at + ROW]
        note = f"  ; {item.kind}" if at == 0 and item.kind == "unreached" else ""
        lines.append(f"  {item.offset + at:04x}  db {row.hex(' ')}{note}")
    return lines


def listing(data: bytes, decode: Callable[[bytes], str], show_bytes: bool = False) -> list[str]:
    walk = walk_room(data)
    items = disassemble(walk)
    labels = {t: f"L{t:04x}" for ins in walk.code.values() for t in ins.targets}
    labels |= {e.offset: f"L{e.offset:04x}" for e in walk.entries}
    labels |= {t: f"T{t:04x}" for ins in walk.code.values() for t in ins.texts}
    labels |= {o: f"D{o:04x}" for ins in walk.code.values() for o, _ in ins.data}
    notes: dict[int, list[str]] = {}
    for entry in walk.entries:
        notes.setdefault(entry.offset, []).append(entry.what)

    def text(offset: int) -> str:
        return decode(data[offset : offset + text_length(data, offset)])

    lines = [f"; {len(data):#x} bytes, header {walk.header_length:#x}, {len(walk.code)} instructions"]
    lines += [f"; {e.what}: L{e.offset:04x}" for e in walk.entries]
    for item in items:
        lines += _label(item.offset, labels, notes)
        if isinstance(item, Data):
            lines += _data_lines(item, decode)
            continue
        shown, extra = _instruction(item, text)
        note = f"  ; {' / '.join(extra)}" if extra else ""
        lines.append(f"  {item.offset:04x}{_raw(data, item.offset, item.size, show_bytes)}  {shown}{note}")
    lines += [f"; error: {error}" for error in walk.errors]
    return lines


def main(argv: Sequence[str] | None = None, echo: Callable[[str], None] = print) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("room", type=int)
    parser.add_argument("--fr", action="store_true", help="the French build (build/bl.ips applied)")
    parser.add_argument("--bytes", action="store_true", help="show each instruction's bytes")
    args = parser.parse_args(argv)
    if not 0 <= args.room < ROOMS:
        parser.error(f"rooms go from 0 to {ROOMS - 1}")
    for line in listing(load_room(args.room, args.fr), text_decoder(args.room, args.fr), args.bytes):
        echo(line)


if __name__ == "__main__":
    main()
