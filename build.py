#!/usr/bin/env python3
import struct

import os
from a816.cpu.cpu_65c816 import RomType, snes_to_rom
from a816.program import Program
from a816.writers import IPSWriter

from script import Table

from utils.dump_battle_rooms import build_battle_text_patch
from utils.dump_rooms import build_text_patch
from utils.inline_strings import insert_dragon_feed_inline_strings, insert_battle_commands_strings


def build_assembly(input, output, writer):
    asm = Program()
    asm.resolver.rom_type = RomType.high_rom
    asm.assemble_with_emitter(input, writer)


# def build_room(input, output):
#     asm = Program()
#     asm.resolver.rom_type = RomType.high_rom
#     buffer = BytesIO()
#     sfc_emiter = SFCWriter(buffer)
#     asm.assemble_with_emitter(input, sfc_emiter)
#
#     buffer.seek(0)
#     uncompressed_data = buffer.read()
#
#     with open('/tmp/uncompressed.bin', 'wb') as uncompressed:
#         uncompressed.write(uncompressed_data)
#
#     with open(output, 'wb') as fd:
#         compressed = lz_compress(uncompressed_data) + b'\x00'
#         compressed = struct.pack('<H', len(compressed) - 1) + compressed
#         # fd.write()
#         # fd.write(compressed)
#         fd.write(compressed)

if __name__ == '__main__':
    lang = 'mz'
    table_path = os.path.join(os.path.dirname(__file__), 'text/table')
    table = Table(os.path.join(table_path, f'{lang}.tbl'))
    with open('bl.ips', 'wb') as f:
        writer = IPSWriter(f, check_for_overlap=True)
        writer.begin()

        with open('bl.sfc', 'rb') as rom:
            build_text_patch(rom, table, writer)
            build_battle_text_patch(rom, table, writer)

        with open('src_assets/8x8_battle.dat', 'rb') as battle_font:
            writer.write_block(battle_font.read(), 0x261B40)

        with open('src_assets/8x8_font.dat', 'rb') as small_font:
            writer.write_block(small_font.read(), 0x8A000)

        insert_dragon_feed_inline_strings(writer, snes_to_rom(0xFC0000))
        insert_battle_commands_strings(writer, snes_to_rom(0xFD0000))
        build_assembly('bl.s', './bl.ips', writer)

        writer.end()
