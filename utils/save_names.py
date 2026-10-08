"""
Give a save file's party the French default names, so a save made with the Japanese (or another) game shows them.

Saves live in SRAM page 0 (30:6000, the first 8 KB of the .srm whatever its size): four 0x5C8-byte slots at
6000/65C8/6B90/7158 (`EED09B`), each a copy of the game state buffer 7E:E800. A slot's byte 8 is its chapter, FF
when empty. The party names 0-9 (7E2B00) sit at slot + 0x2F0, 8 codes each, padded with FF. The game checks a 16-bit
sum of the words 6000-7EFF against 7FF0 (`EED18A`), so the sum is written again.

    python -m utils.save_names SAVE.srm [-o OUT.srm]
"""

import argparse
import struct
import sys
from pathlib import Path

from script import Table

from utils.name_tables import encode, read_names

SLOTS = (0x0000, 0x05C8, 0x0B90, 0x1158)  # 6000-based offsets of the four save slots
CHAPTER = 0x08  # FF: empty slot
NAMES = 0x2F0  # the party names in a slot
NAME_COUNT = 10  # 7E2B00: Byuu, Yoyo and the dragons, the names the player can change
NAME_SIZE = 8
EMPTY = 0xFF
CHECKSUM = 0x1FF0
CHECKSUM_WORDS = 0xF80  # 6000-7EFF
TABLE = Path("text/table/mz.tbl")
DEFAULT_NAMES = Path("text/fr/names.xml")


def name_record(table: Table, name: str) -> bytes:
    return encode(table, name)[:NAME_SIZE].ljust(NAME_SIZE, bytes([EMPTY]))


def checksum(sram: bytes) -> int:
    return sum(struct.unpack_from(f"<{CHECKSUM_WORDS}H", sram)) & 0xFFFF


def used_slots(sram: bytes) -> list[int]:
    return [slot for slot in SLOTS if sram[slot + CHAPTER] != EMPTY]


def rename(sram: bytes, records: list[bytes]) -> bytes:
    """`sram` with every used slot's party names set to `records`, and the checksum updated."""
    out = bytearray(sram)
    for slot in used_slots(sram):
        start = slot + NAMES
        out[start : start + NAME_COUNT * NAME_SIZE] = b"".join(records[:NAME_COUNT])
    struct.pack_into("<H", out, CHECKSUM, checksum(bytes(out)))
    return bytes(out)


def names_in(table: Table, sram: bytes, slot: int) -> list[str]:
    start = slot + NAMES
    return [
        table.to_text(sram[start + index * NAME_SIZE : start + (index + 1) * NAME_SIZE].split(bytes([EMPTY]))[0])
        for index in range(NAME_COUNT)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Give a save file's party the French default names.")
    parser.add_argument("save", type=Path, help=".srm file (8 or 32 KB)")
    parser.add_argument("-o", "--output", type=Path, help="where to write the result (default: in place)")
    args = parser.parse_args()

    data = args.save.read_bytes()
    sram, rest = data[:0x2000], data[0x2000:]
    if checksum(sram) != struct.unpack_from("<H", sram, CHECKSUM)[0]:
        print(f"{args.save}: checksum mismatch, not a Bahamut Lagoon save", file=sys.stderr)
        return 1
    table = Table(str(TABLE))
    records = [name_record(table, name) for name in read_names(DEFAULT_NAMES)]
    for slot in used_slots(sram):
        print(f"slot {SLOTS.index(slot)} (chapter {sram[slot + CHAPTER]}): {', '.join(names_in(table, sram, slot))}")
    patched = rename(sram, records)
    (args.output or args.save).write_bytes(patched + rest)
    print("now:", ", ".join(names_in(table, patched, used_slots(patched)[0])) if used_slots(patched) else "no save")
    return 0


if __name__ == "__main__":
    sys.exit(main())
