import re
import struct
import os

from a816.cpu.cpu_65c816 import snes_to_rom
from script import Table

from utils.dump_rooms import compress_room
from utils.lz import lz_decompress_battle
from utils.vm import AlreadyVisitedError
from utils.vm.executor import walk_event_chain
from utils.vm.opcodes import bl_prefix_lookup_chars
from utils.vm.opcodes_map import battle_opcode_table, battle_opcode_names
from utils.vm.room import Room, prettify
import xml.etree.ElementTree as ET


def decompress_block(rom):
    size = rom.read(2)
    size = struct.unpack('<H', size)[0]
    print(hex(size))
    data = rom.read(size)
    decompressed = bytearray()
    decompressed = lz_decompress_battle(data, decompressed)

    def get_size(count, control_byte):
        size = 0
        for i in range(count):
            if (control_byte >> i) & 1:
                size += 2
            else:
                size += 1
        return size + 1

    while True:
        control = rom.read(1)

        if control[0] != 0:
            next_end = rom.read(2)
            control_byte = rom.peek(1)

            next_size = get_size(control[0], control_byte[0])
            data = rom.read(next_size)

            decompressed = lz_decompress_battle(data, decompressed)
        else:
            break
    return decompressed


def simulate_run(decompressed, run_opcode_addresses):
    opcodes = {}
    sorted_run_to_first_text = sorted(run_opcode_addresses)
    for k in range(len(sorted_run_to_first_text)):
        op_addr = sorted_run_to_first_text[k]

        opcode = decompressed[op_addr - 0x7FC080]
        try:
            # print(hex(op_addr - 0x7FC000))
            opcodes[opcode] = sorted_run_to_first_text[k + 1] - op_addr
            # print('{:#02x}: Opcode({}),'.format(opcode, sorted_run_to_first_text[k + 1] - op_addr))
        except IndexError:
            print(f'{opcode:#02x}')

    for key in sorted(opcodes.keys()):
        print(f'{opcode:#02x}: Opcode({opcodes[key]}),')


def walk_battle_room(room_id, decompressed, table, lang):
    addr = struct.unpack('<H', decompressed[:2])[0]

    decompressed_program = decompressed[addr:]
    room = Room(decompressed_program, battle_opcode_table, battle_opcode_names, table, lang=lang)
    room.id = room_id
    ptr_table = []
    for k in range(0, 0x0c + 2):
        room.pc = 0
        try:
            addr = room.get_word(k * 2)
            room.program.put_reference(k * 2, addr, f"entry {k:#02x}")

            room.jump_to(addr)
            # print('PC {:04x} {}'.format(addr, k))

            walk_event_chain(room)
        except AlreadyVisitedError:
            pass

    return room

    # program.display_program_part(stdout, text_program)
    # with open('/tmp/b{}.txt'.format(room.id), 'w', encoding='utf-8') as output:
    #     room.program.display_program(output)


def extract_string_from_block(lang, table, data, index):
    pos = index
    while True:
        if pos >= len(data):
            pos = len(data)
            break
        if data[pos] == 0xFF:
            pos += 1
            break
        if data[pos] == 0xFD:
            pos += 2
            break
        pos += 1

    if lang == 'jp':
        text_data = bl_prefix_lookup_chars(bytes(data[index:pos]))
    else:
        text_data = bytes(data[index:pos])

    return pos, table.to_text(text_data).replace('\\s', ' ')


def get_battle_room(rom, room_id, table, lang):
    table_entry = snes_to_rom(0xc7140f)
    rom.seek(table_entry + (room_id * 3))
    ptr = rom.read(3)
    address = snes_to_rom(ptr[0] + (ptr[1] << 8) + (ptr[2] << 16))

    rom.seek(address)
    try:
        decompressed = decompress_block(rom)
        addr = struct.unpack('<H', decompressed[:2])[0]
        decompressed_data = decompressed[:addr]
        decompressed_program = decompressed[addr:]

        room = Room(decompressed_program, battle_opcode_table, battle_opcode_names, table, lang=lang)
    except IndexError as e:
        print(f'Unable to decompress: {e}')
    else:
        return address, decompressed_data, room


def debug_dump_first_battle_room_data():
    lang = 'jp'
    with open(os.path.join(os.path.dirname(__file__), f'../bl_{lang}.sfc'), 'rb') as rom:
        def get_pointer(room_id):
            table_entry = snes_to_rom(0xc7140f)
            rom.seek(table_entry + (room_id * 3))
            ptr = rom.read(3)
            return snes_to_rom(ptr[0] + (ptr[1] << 8) + (ptr[2] << 16))

        room_0_pointer = get_pointer(0)
        room_1_pointer = get_pointer(1)
        rom.seek(room_0_pointer)
        data = rom.read(room_1_pointer - room_0_pointer)

        with open('/tmp/battle_0_raw_compressed.bin', 'wb') as f:
            f.write(data)


def dump_battle_room(rom, room_id, table, lang, output_dir):
    table_entry = snes_to_rom(0xc7140f)
    rom.seek(table_entry + (room_id * 3))
    ptr = rom.read(3)
    address = snes_to_rom(ptr[0] + (ptr[1] << 8) + (ptr[2] << 16))

    rom.seek(address)
    try:
        decompressed = decompress_block(rom)
        with open('/tmp/decompressed.bin', 'wb') as f:
            f.write(decompressed)
    except IndexError as e:
        print(f'Unable to decompress: {e}')
    else:
        try:
            room = walk_battle_room(room_id, decompressed, table, lang)
            program = room.program
            # override_strings = None
            # if room.lang == 'fr':
            #     text_program = room.program.filter(lambda _, e: e[0][0] == 'text')
            #     first_text_address = sorted(text_program.keys())[0]
            #     text_block = room.room[first_text_address:]
            #     pos = 0
            #     strings = []
            #     # print(room.table.to_text(bytes(text_block)).replace('\s', ' '))
            #     while pos < len(text_block):
            #         pos, string = extract_string_from_block(lang, room.table, text_block, pos)
            #         strings.append(string)
            #
            #     override_strings = strings
            #
            texts = room.dump_text()
            if texts:
                with open(os.path.join(output_dir, f'{room_id:04d}.xml'), 'wt', encoding='utf-8') as output:
                    output.write(prettify(texts))
        except AlreadyVisitedError:
            pass

        with open('/tmp/battle.bin', 'wb') as out:
            out.write(decompressed)


def build_battle_text_patch(rom, table, writer):
    xmlfile_re = re.compile('(\d+)\.xml')
    dialog_dir = os.path.join(os.path.dirname(__file__), '../text/battle')
    files = os.listdir(dialog_dir)

    for file in files:
        match = xmlfile_re.match(file)
        if match:
            room_id = int(match.group(1))
            address, data, room = get_battle_room(rom, room_id, table, 'jp')
            tree = ET.parse(os.path.join(dialog_dir, file))
            updated_room = room.update_text(tree)
            battle_room_data = data + updated_room

            compressed = compress_room(battle_room_data) + b'\x00' # no next block
            print('compressed', hex(len(compressed)))

            writer.write_block(compressed, address)

            # value = rom_to_snes(address, RomType.high_rom)

            # writer.write_block(struct.pack('<HB', value & 0xFFFF, (value >> 16) & 0xFF),
            #                    snes_to_rom(0xDA8000) + (room_id * 3))


def output_dir(lang):
    return os.path.join(os.path.dirname(__file__), f'../text/{lang}/battle')


def dump_rooms_for_lang(lang):
    table_path = os.path.join(os.path.dirname(__file__), '../text/table')

    table = Table(os.path.join(table_path, f'{lang}.tbl'))
    with open(os.path.join(os.path.dirname(__file__), f'../bl_{lang}.sfc'), 'rb') as rom_file:
        for room_id in range(32):
            dump_battle_room(rom_file, room_id, table, lang, output_dir=output_dir(lang))


def debug_dump_room(lang='jp'):
    table_path = os.path.join(os.path.dirname(__file__), '../text/table')

    table = Table(os.path.join(table_path, f'{lang}.tbl'))

    with open(os.path.join(os.path.dirname(__file__), f'../bl_{lang}.sfc'), 'rb') as rom_file:
        # for room_id in range(32):
        room_id = 0
        dump_battle_room(rom_file, room_id, table, lang, output_dir=output_dir(lang))


def debug_compress_battle_room(lang='jp'):
    table_path = os.path.join(os.path.dirname(__file__), '../text/table')

    table = Table(os.path.join(table_path, f'{lang}.tbl'))

    with open(os.path.join(os.path.dirname(__file__), f'../bl_{lang}.sfc'), 'rb') as rom_file:
        address, data, room = get_battle_room(rom_file, 0, table, 'jp')
        battle_room_data = data + room.room

        compressed = compress_room(battle_room_data)
        with open('/tmp/recompressed.bin', 'wb') as f:
            f.write(compressed)


if __name__ == '__main__':
    # debug_dump_first_battle_room_data()
    # debug_dump_room()
    # debug_compress_battle_room()

    # dump_rooms_for_lang('fr')
    dump_rooms_for_lang('en')
    # dump_rooms_for_lang('jp')
