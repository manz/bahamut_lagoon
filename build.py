#!/usr/bin/env python3
import argparse
import os
import struct

from a816.cpu.cpu_65c816 import RomType, rom_to_snes, snes_to_rom
from a816.program import Program
from a816.writers import IPSWriter
from script import Table
from utils.decompress_gfx import lz_compress_gfx
from utils.dump_battle_rooms import build_battle_text_patch
from utils.dump_rooms import build_text_patch
from utils.inline_strings import (insert_battle_commands_strings,
                                  insert_battle_fixed, insert_char_names,
                                  insert_dragon_feed_inline_strings,
                                  insert_inline_strings,
                                  insert_messages_strings)


def build_assembly(input, output, writer):
    asm = Program()
    asm.resolver.rom_type = RomType.high_rom
    asm.assemble_with_emitter(input, writer)
    return asm


class DebugWriter(IPSWriter):
    def write_block_header(self, block, block_address):
        super().write_block_header(block, block_address)
        print(f'DEBUGIPS: {rom_to_snes(block_address, RomType.high_rom):#x} {len(block):#x}')


def build_rooms_partials(writer, table):
    with open('bl.sfc', 'rb') as rom:
        address = build_text_patch(rom, table, writer, snes_to_rom(0xF00000))
        print(f'Relocated dialog rooms end at {address + 0xC00000:#0x}')

        address = build_battle_text_patch(rom, table, writer, address)
        print(f'Relocated battle rooms end at {address + 0xC00000:#0x}')


partials_builder = {
    'rooms': build_rooms_partials
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build patch.')

    parser.add_argument('--debug', dest='debug', action='store_true',
                        help='Turns debug on')

    parser.add_argument('--rooms', action='store_true',
                        help='build rooms partial')

    args = parser.parse_args()

    lang = 'mz'
    table_path = os.path.join(os.path.dirname(__file__), 'text/table')
    table = Table(os.path.join(table_path, f'{lang}.tbl'))

    if args.rooms:
        with open('rooms.partial', 'wb') as partial:
            writer = IPSWriter(partial, check_for_overlap=True)
            build_rooms_partials(writer, table)
    else:
        with open('bl.ips', 'wb') as f:
            writer = IPSWriter(f, check_for_overlap=True)
            writer.begin()

            if os.path.exists('rooms.partial'):
                with open('rooms.partial', 'rb') as partial:
                    f.write(partial.read())
            else:
                build_rooms_partials(writer, table)

            program = build_assembly('bl.s', './bl.ips', writer)
            # get address for draw_inline_string_patched for code generation.
            draw_inline_string_ref = program.resolver.current_scope['draw_inline_string_patched']

            insert_dragon_feed_inline_strings(writer, snes_to_rom(0xFC0000))
            end_of_battle_commands = insert_battle_commands_strings(writer, snes_to_rom(0xFD0000))
            end_of_inline_strings = insert_inline_strings(writer, snes_to_rom(end_of_battle_commands + 1),
                                                          draw_inline_string_ref)

            end_of_message_strings = insert_messages_strings(writer, snes_to_rom(end_of_inline_strings + 1))

            # too much ? maybe
            # with open('src_assets/e89a4f.bin', 'rb') as asset:
            #     data = asset.read()
            #     compressed = lz_compress_gfx(data)
            #     writer.write_block(compressed, snes_to_rom(end_of_message_strings + 1))
            # .D5:E6B9                 LDA     #$9A4F
            # .D5:E6BC                 STA     D, $28
            # .D5:E6BE                 SEP     #$20 ; ' '
            # .D5:E6C0 .A8
            # .D5:E6C0                 LDA     #$E8 ; 'Þ'
            writer.write_block(struct.pack('<H', end_of_message_strings + 1 & 0xFFFF), snes_to_rom(0xD5E6B9 + 1))
            writer.write_block(struct.pack('B', (end_of_message_strings + 1) >> 16), snes_to_rom(0xD5E6C0 + 1))

            insert_char_names(writer)
            insert_battle_fixed(writer)

            writer.end()
