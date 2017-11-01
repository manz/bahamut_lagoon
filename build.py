#!/usr/bin/env python3
import struct

import os
from a816.cpu.cpu_65c816 import RomType, snes_to_rom
from a816.program import Program
from a816.writers import IPSWriter

from script import Table

from utils.dump_battle_rooms import build_battle_text_patch
from utils.dump_rooms import build_text_patch
from utils.inline_strings import insert_dragon_feed_inline_strings, insert_battle_commands_strings, insert_char_names, \
    insert_inline_strings, insert_messages_strings, insert_battle_fixed


def build_assembly(input, output, writer):
    asm = Program()
    asm.resolver.rom_type = RomType.high_rom
    asm.assemble_with_emitter(input, writer)
    return asm


if __name__ == '__main__':
    lang = 'mz'
    table_path = os.path.join(os.path.dirname(__file__), 'text/table')
    table = Table(os.path.join(table_path, f'{lang}.tbl'))
    with open('bl.ips', 'wb') as f:
        writer = IPSWriter(f, check_for_overlap=True)
        writer.begin()

        with open('bl.sfc', 'rb') as rom:
            address = build_text_patch(rom, table, writer, snes_to_rom(0xF00000))
            print(f'Relocated dialog rooms end at {address + 0xC00000:#02x}')

            address = build_battle_text_patch(rom, table, writer, address)

            print(f'Relocated battle rooms end at {address + 0xC00000:#02x}')

        with open('src_assets/8x8_battle.dat', 'rb') as battle_font:
            writer.write_block(battle_font.read(), 0x261B40)

        with open('src_assets/8x8_font.dat', 'rb') as small_font:
            writer.write_block(small_font.read(), 0x8A000)

        program = build_assembly('bl.s', './bl.ips', writer)
        # get address for draw_inline_string_patched for code generation.
        draw_inline_string_ref = program.resolver.current_scope['draw_inline_string_patched']

        insert_dragon_feed_inline_strings(writer, snes_to_rom(0xFC0000))
        end_of_battle_commands = insert_battle_commands_strings(writer, snes_to_rom(0xFD0000))
        end_of_inline_strings = insert_inline_strings(writer, snes_to_rom(end_of_battle_commands + 1),
                                                      draw_inline_string_ref)

        insert_messages_strings(writer, snes_to_rom(end_of_inline_strings + 1))
        insert_char_names(writer)
        insert_battle_fixed(writer)

        writer.end()
