"""Item names: dump the vanilla table to text/items.xml and insert it back."""

import xml.etree.ElementTree as ET

from a816.writers import Writer
from script import Table

from utils.cartridge import rom_offset
from utils.vm.room import prettify

ITEM_NAMES = 0xEF3CA0  # 128 records: icon byte, then the name
ITEM_COUNT = 128
RECORD_SIZE = 9
NAME_SIZE = RECORD_SIZE - 1  # up to 8 cells, FF-terminated when shorter, FE-padded
END = 0xFF
PADDING = 0xFE


def dump_item_names(rom: bytes, table: Table) -> str:
    """The item name table as XML: one <string icon="0x.."> per record."""
    root = ET.Element("item_names", pointers=hex(ITEM_NAMES))
    offset = rom_offset(ITEM_NAMES)
    for index in range(ITEM_COUNT):
        record = rom[offset + index * RECORD_SIZE : offset + (index + 1) * RECORD_SIZE]
        name = record[1:]
        end = name.find(END)
        string = ET.SubElement(root, "string", icon=f"{record[0]:#04x}")
        string.text = table.to_text(name if end < 0 else name[:end])
    return prettify(root)


def item_name_records(xml: str, table: Table) -> bytes:
    """The item name table bytes for the names in xml."""
    root = ET.fromstring(xml)
    data = b""
    for string in root:
        name = table.to_bytes(string.text or "")
        if len(name) > NAME_SIZE:
            raise ValueError(f"item name {string.text!r} is {len(name)} cells, the table holds {NAME_SIZE}")
        if len(name) < NAME_SIZE:
            name += bytes([END])
        icon = string.get("icon")
        if icon is None:
            raise ValueError(f"item name {string.text!r} has no icon")
        data += bytes([int(icon, 16)]) + name.ljust(NAME_SIZE, bytes([PADDING]))
    if len(data) != ITEM_COUNT * RECORD_SIZE:
        raise ValueError(f"expected {ITEM_COUNT} item names, got {len(data) // RECORD_SIZE}")
    return data


def insert_item_names(writer: Writer, table: Table, path: str = "./text/items.xml") -> None:
    with open(path, encoding="utf-8") as source:
        writer.write_block(item_name_records(source.read(), table), rom_offset(ITEM_NAMES))
