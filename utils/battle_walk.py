"""Walk the battle scripts from where the game enters them: the 14 header entries, following jumps and calls.
What the walk never reaches between the header and the first text is code no entry runs (or data the walk does
not know about). Also lists the texts the scripts show, by address and by text-table index.

    uv run python -m utils.battle_walk [ROOM ...]
"""

from __future__ import annotations

import argparse
import struct
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from utils.cartridge import rom_offset
from utils.dump_battle_rooms import decompress_block
from utils.vm.battle_script import STOPS, Instruction, header, instruction

ROM = Path(__file__).parents[1] / "build/bl.sfc"
ROOM_TABLE = 0xC7140F
ROOMS = 32
HEADER_SIZE = 0x20


def room_block(room_id: int, rom_path: Path = ROM) -> bytes:
    """Battle room `room_id` as unpacked to $7F:C080."""
    with rom_path.open("rb") as rom:
        rom.seek(rom_offset(ROOM_TABLE) + room_id * 3)
        ptr = rom.read(3)
        rom.seek(rom_offset(ptr[0] | ptr[1] << 8 | ptr[2] << 16))
        return bytes(decompress_block(rom))


def room_script(room_id: int, rom_path: Path = ROM) -> bytes:
    """The script of battle room `room_id`: the unpacked room from its base (its first word)."""
    block = room_block(room_id, rom_path)
    base: int = struct.unpack("<H", block[:2])[0]
    return block[base:]


@dataclass
class Walk:
    code: dict[int, Instruction]  # every reached instruction by address
    labels: set[int]  # entries and jump targets
    area_table: int
    text_table: int
    texts: set[int] = field(default_factory=set)  # text addresses, direct or through the text table

    def reached_bytes(self) -> int:
        return sum(i.size for i in self.code.values())

    def code_end(self) -> int:
        """Where the code area ends: the area-trigger table, the text table and the texts follow the code."""
        return min({self.area_table, self.text_table} | self.texts)

    def unreached(self) -> list[tuple[int, int]]:
        """Address ranges [start, end) of the code area no reached instruction covers."""
        gaps, at = [], HEADER_SIZE
        for lo, hi in sorted((o, o + i.size) for o, i in self.code.items()):
            if lo > at:
                gaps.append((at, lo))
            at = max(at, hi)
        if at < self.code_end():
            gaps.append((at, self.code_end()))
        return gaps


def walk(data: bytes) -> Walk:
    head = header(data)
    result = Walk({}, set(), head.area_table, head.text_table)
    todo = [e for e in head.entries if e < len(data)]
    result.labels.update(todo)
    while todo:
        pos = todo.pop()
        while pos < len(data) and pos not in result.code:
            ins = instruction(data, pos)
            result.code[pos] = ins
            todo += ins.targets
            result.labels.update(ins.targets)
            if ins.text is not None:
                result.texts.add(ins.text)
            if ins.text_index is not None:
                result.texts.add(head.text(data, ins.text_index))
            if ins.name in STOPS:
                break
            pos += ins.size
    return result


def report(room_id: int, data: bytes) -> list[str]:
    w = walk(data)
    total = w.code_end() - HEADER_SIZE
    lines = [
        f"room {room_id:2d}: {w.reached_bytes()}/{total} code bytes reached ({100 * w.reached_bytes() / total:.1f}%)"
    ]
    lines += [f"  unreached {lo:04x}-{hi - 1:04x} ({hi - lo} bytes)" for lo, hi in w.unreached()]
    return lines


def main(argv: list[str] | None = None, echo: Callable[[str], None] = print) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rooms", type=int, nargs="*")
    args = parser.parse_args(argv)
    reached = total = 0
    for room_id in args.rooms or range(ROOMS):
        data = room_script(room_id)
        w = walk(data)
        reached, total = reached + w.reached_bytes(), total + w.code_end() - HEADER_SIZE
        for line in report(room_id, data):
            echo(line)
    echo(f"all: {reached}/{total} code bytes reached ({100 * reached / total:.1f}%)")


if __name__ == "__main__":
    main()
