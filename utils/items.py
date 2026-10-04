import xml.etree.ElementTree as ET

from script import Table

from utils.cartridge import rom_offset


def dump_inline_string(rom_file, root, xref):
    rom_file.seek(rom_offset(xref) + 3)
    raw_string = b""
    while rom_file.peek(2)[:2] != b"\xff\xff":
        raw = rom_file.read(2)
        if raw != b"\x81\x40":
            raw_string += raw
        else:
            raw_string += b"\x20"

    jap_text = raw_string.decode("shift-jis")
    string = ET.SubElement(inline, "string")
    string.set("ref", hex(xref))
    string.text = jap_text


if __name__ == "__main__":
    with open("../bl.sfc", "rb") as rom_file:
        Table("../texts/")
