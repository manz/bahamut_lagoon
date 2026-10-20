"""
The 8-byte name tables (characters, classes, dragons, enemies) and the full names small_vwf draws instead.

Every engine indexes these tables as base + id * 8, so the records keep their size and hold the name cut to eight
codes. The full names go in a generated a816 module: small_vwf_render, handed a record's address, reads the full
name in its place.
"""

import xml.etree.ElementTree as ET
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from a816.writers import Writer
from script import Table

from utils.cartridge import rom_offset
from utils.small_vwf_bake import GLYPH, SHADOW_GAP, Baked, bake

RECORD = 8
SPELL_WIDTH = 75  # pixels: Frappe de foudre, the widest spell name the lists and the banner fit (docs/glossary.md)
END = 0xFF
PAD = 0xFE


@dataclass(frozen=True)
class NameTable:
    label: str
    source: Path
    address: int  # bus address of record 0's name
    record: int = RECORD  # bytes from one record to the next


NAME_TABLES = (
    NameTable("char_names", Path("text/fr/names.xml"), 0xEF0380),
    NameTable("enemy_names", Path("text/enemies.xml"), 0xEF1F50),
    NameTable("class_names", Path("text/classes.xml"), 0xEF6360),
    NameTable("dragon_names", Path("text/dragons.xml"), 0xEF63D8),
    NameTable("spell_names", Path("text/spells.xml"), 0xEF5920),
)
ITEM_NAMES = Path("text/items.xml")
BAKED_TILES = Path("build/gen/small_vwf_baked.bin")  # the tiles long_names_source's entries point into (small_vwf.s)
ITEM_RECORDS = 0xEF3CA0  # icon, then the name cut to a record
ITEM_TABLE = NameTable("item_names", ITEM_NAMES, ITEM_RECORDS + 1, 1 + RECORD)  # the names, past each icon


def read_names(source: Path) -> list[str]:
    return [(string.text or "").removesuffix("[0xff]") for string in ET.parse(source).getroot()]


SMALL_FONT_FOLD = str.maketrans("ÀÂÇÈÉÊËÎÏÔÙÛ", "AACEEEEIIOUU")  # small_font has no accented capitals


def encode(table: Table, name: str) -> bytes:
    """A name in the 8x8 text codes, accented capitals folded to the letters small_font draws."""
    return table.to_bytes(name.translate(SMALL_FONT_FOLD).replace(" ", r"\s"))


def width(font: bytes, codes: bytes) -> int:
    """The pixels small_vwf's pen moves over `codes` up to their end, the shadow's gap after each glyph included."""
    pen = 0
    for code in codes:
        if code >= PAD:
            break
        pen += font[code * GLYPH + 8] + SHADOW_GAP
    return pen


def short_record(codes: bytes) -> bytes:
    """The name cut to a record: up to eight codes, FF-terminated when shorter, FE-padded."""
    record = codes[:RECORD]
    if len(record) < RECORD:
        record += bytes([END])
    return record.ljust(RECORD, bytes([PAD]))


def insert_short_names(writer: Writer, table: Table) -> None:
    for name_table in NAME_TABLES:
        records = b"".join(short_record(encode(table, name)) for name in read_names(name_table.source))
        writer.write_block(records, rom_offset(name_table.address))


def item_records(table: Table, source: Path = ITEM_NAMES) -> bytes:
    """Item name records: the icon code, then the name as short_record cuts it."""
    records = b""
    for string in ET.parse(source).getroot():
        icon = string.get("icon")
        if icon is None:
            raise ValueError(f"item name {string.text!r} has no icon")
        records += bytes([int(icon, 16)]) + short_record(encode(table, string.text or ""))
    return records


def insert_item_names(writer: Writer, table: Table) -> None:
    writer.write_block(item_records(table), rom_offset(ITEM_RECORDS))


def baked_fields(baked: Baked) -> str:
    return f"offset = 0x{baked.offset:04X}, cells = {baked.cells}"


def baked_entry(baked: Baked) -> list[str]:
    return [f"    .istruct BakedEntry {{ {baked_fields(baked)} }}"]


def long_names_source(
    table: Table, font: bytes, segments: list[bytes], statics: Sequence[tuple[int, bytes]] = ()
) -> tuple[str, bytes]:
    """The a816 module of full names: a descriptor per table (record 0, count, pointers, record size, baked tiles),
    then the strings and each name's baked entry (offset in small_vwf_baked_tiles, cells), then the inline string
    segments' entries by baked id (small_vwf_inline_baked), then the static strings in bank FD by address
    (small_vwf_static_baked: a count, then the address's low word, the length, 0 and the baked entry); and the baked
    tiles."""
    descriptors = []
    pointers = []
    strings = []
    entries = []
    blob = bytearray()
    offsets: dict[bytes, int] = {}
    for name_table in (*NAME_TABLES, ITEM_TABLE):
        names = read_names(name_table.source)
        descriptors += [
            "    .istruct LongNameTable {",
            f"        record = 0x{name_table.address:06X}",
            f"        count = {len(names)}",
            f"        pointers = _{name_table.label}",
            f"        record_size = {name_table.record}",
            f"        baked = _{name_table.label}_baked",
            "    }",
        ]
        pointers.append(f"_{name_table.label}:")
        entries.append(f"_{name_table.label}_baked:")
        for (index, name), baked in zip(
            enumerate(names), bake(font, [encode(table, name) for name in names], blob, offsets), strict=True
        ):
            label = f"_{name_table.label}_{index}"
            pointers.append(f"    .dw {label}")
            codes = ", ".join(f"0x{code:02X}" for code in (*encode(table, name), END))
            strings += [f"{label}:", f"    .db {codes}"]
            entries += baked_entry(baked)
    entries.append("small_vwf_inline_baked:")
    for baked in bake(font, segments, blob, offsets):
        entries += baked_entry(baked)
    entries += ["small_vwf_static_baked:", f"    .dw {len(statics)}", "small_vwf_static_entries:"]
    for (address, static_codes), baked in zip(
        statics, bake(font, [static_codes for _, static_codes in statics], blob, offsets), strict=True
    ):
        entries.append(
            f"    .istruct StaticBaked {{ address = 0x{address & 0xFFFF:04X}, length = {len(static_codes)},"
            f" baked = {{ {baked_fields(baked)} }} }}"
        )
    source = "\n".join(
        [
            '"""Full names small_vwf reads in place of the 8-byte records, and where their baked tiles are. Generated by build.py."""',
            "",
            '.include "src/expansion.i"',
            '.include "src/name_tables.i"',
            "",
            ".alloc long_names in expansion {",
            "long_name_tables:",
            *descriptors,
            "    .dl 0x000000",
            *pointers,
            *strings,
            *entries,
            "}",
            "",
            ".pool small_vwf_baked {",
            "    range 0xFB0000 0xFBFFFF",
            "    strategy order",
            "}",
            "",
            ".alloc small_vwf_baked_tiles in small_vwf_baked {",
            f'    .incbin "{BAKED_TILES}"',
            "}",
            "",
        ]
    )
    return source, bytes(blob)
