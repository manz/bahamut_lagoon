import struct
import os
import math
import re

from a816.cpu.cpu_65c816 import snes_to_rom, rom_to_snes, RomType
from script import Table

from utils.disasm import live_disasm
from utils.lz import lz_decompress, lz_compress
from utils.vm.opcodes_map import opcode_table, opcode_names
from utils.vm.room import Room, prettify
import xml.etree.ElementTree as ET


def battle_decompress_block(rom):
    origin = rom.tell()

    size = rom.read(2)
    size = struct.unpack('<H', size)[0]
    print(hex(size))
    data = rom.read(size)
    decompressed = bytearray()
    decompressed = lz_decompress(data, decompressed)

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

        if control[0] & 0x3f:
            next_end = rom.read(2)
            control_byte = rom.peek(1)

            next_size = get_size(control[0], control_byte[0])
            data = rom.read(next_size)

            decompressed = lz_decompress(data, decompressed)
        else:
            break
    return decompressed


def decompress_block(rom):
    size = rom.read(2)
    size = struct.unpack('<H', size)[0]

    data = rom.read(size)
    decompressed = bytearray()
    decompressed = lz_decompress(data, decompressed)

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

        if control[0] & 0x3f:
            next_end = rom.read(2)
            next_end = struct.unpack('<H', next_end)[0]
            control_byte = rom.peek(1)

            next_size = get_size(control[0], control_byte[0])
            data = rom.read(next_size)

            decompressed = lz_decompress(data, decompressed)
        else:
            break
    return decompressed


def compress_room(data):
    compressed = lz_compress(data)
    size_header = struct.pack('<H', len(compressed))
    return size_header + compressed


def is_compressed(rom, room_id):
    room_id_high = 1 << (room_id & 0x07)
    room_id_low = room_id >> 3

    rom.seek(snes_to_rom(0xDA8300) + room_id_low)
    return (struct.unpack('B', rom.read(1))[0] & room_id_high) != 0


def get_dialog_room(rom, room_id, table, lang='jp', disasm=False):
    """used for rebuild script"""
    rom.seek(snes_to_rom(0xDA8000) + (room_id * 3))
    ptr = rom.read(3)

    rom.seek(snes_to_rom(ptr[0] + (ptr[1] << 8) + (ptr[2] << 16)))

    decompressed = decompress_block(rom)

    room = Room(decompressed, opcode_table, opcode_names, table, lang)
    room.id = room_id
    room.compressed_size = rom.tell() - snes_to_rom(ptr[0] + (ptr[1] << 8) + (ptr[2] << 16))
    if disasm:
        room = live_disasm(room_id, decompressed, table, lang)
    return room


def dump_room(rom, room, table, output_dir, lang=None):
    rom.seek(room["address"])
    room_id = room['id']
    print(f'room: {room_id}')
    if room['compressed']:
        decompressed = decompress_block(rom)
        # else:
        #     # Might be not necessary but for completion it is implemented
        #     # (results in mostly very short rooms)
        #     decompressed = rom.read(room['size'])

        room = live_disasm(room_id, decompressed, table, lang=lang)
        room.program.display_program()
        texts = room.dump_text()
        if texts:
            with open(os.path.join(output_dir, f'{room_id:04d}.xml'), 'wt', encoding='utf-8') as output:
                output.write(prettify(texts))


# check if room needs decompression
# .DA:156A sub_DA156A:                             ; CODE XREF: .DA:1533p
# .DA:156A                 TDC
# .DA:156B                 LDA     word_7E030F+1 ; orig=0x0310
# .DA:156E                 AND     #7
# .DA:1570                 JSR     math_pow
# .DA:1573                 STA     D,$10
# .DA:1575                 LDA     word_7E030F+1 ; orig=0x0310
# .DA:1578                 LSR
# .DA:1579                 LSR
# .DA:157A                 LSR
# .DA:157B                 JSR     sub_DA071B
# .DA:157E                 LDA     $DA8300,X
# .DA:1582                 BIT     D,$10
# .DA:1584                 BNE     loc_DA1588
# .DA:1586                 CLC
# .DA:1587                 RTS
# .DA:1588 ; ---------------------------------------------------------------------------
# .DA:1588
# .DA:1588 loc_DA1588:                             ; CODE XREF: sub_DA156A+1Aj
# .DA:1588                 SEC
# .DA:1589                 RTS


def math_pow_2(a):
    a = a & 0x0F
    return int(math.pow(2, a))


DANGER = []


def dump_rooms(rom, table, lang, output_dir, room_id=None):
    room_table = build_room_address_table(rom)
    if room_id:
        rooms = [room for room in room_table if room['id'] == room_id]
    else:
        rooms = sorted(room_table, key=lambda r: r['id'])

    for room in rooms:
        if room['id'] not in DANGER:
            dump_room(rom, room,
                      table,
                      output_dir,
                      lang=lang)


def format_dialogs(tree):
    texts = tree.getroot()
    for text in texts:
        if text.get('center') == 'true':
            data = text.find('data')
            tmp = data.text


def build_text_patch(rom, table, writer, reloc_address):
    xmlfile_re = re.compile('(\d+)\.xml')
    dialog_dir = os.path.join(os.path.dirname(__file__), '../text/dialog')
    files = os.listdir(dialog_dir)
    address = reloc_address
    for file in files:
        match = xmlfile_re.match(file)
        if match:
            room_id = int(match.group(1))

            if is_compressed(rom, room_id):
                room = get_dialog_room(rom, room_id, table, 'jp')
                tree = ET.parse(os.path.join(dialog_dir, file))
                updated_room = room.update_text(tree)

                if len(updated_room) >= 0x6000:
                    logger.error(f'Un compressed Room {room_id} is bigger than the ram buffer 0x6000'
                                 ' storing it uncompressed')
                    room_id_high = 1 << (room_id & 0x07)
                    room_id_low = room_id >> 3
                    compressed_byte_address = snes_to_rom(0xDA8300) + room_id_low
                    rom.seek(compressed_byte_address)
                    compressed_byte = room_compressed.get(compressed_byte_address, struct.unpack('B', rom.read(1))[0])
                    room_compressed[compressed_byte_address] = compressed_byte & ~room_id_high
                    logger.error(f'{compressed_byte:02b} {room_compressed[compressed_byte_address]:02b}')
                    updated_room_data = updated_room
                else:
                    updated_room_data = compress_room(updated_room)

                if address & 0xff0000 != (address + len(updated_room_data)) & 0xff0000:
                    address = (address & 0xff0000) + 0x10000

                writer.write_block(updated_room_data, address)

                value = rom_to_snes(address, RomType.high_rom)

                writer.write_block(struct.pack('<HB', value & 0xFFFF, (value >> 16) & 0xFF),
                                   snes_to_rom(0xDA8000) + (room_id * 3))

                address += len(updated_room_data) + 1

    for address, value in room_compressed.items():
        writer.write_block(struct.pack('B', value), address)

    print(f'Ends at {address + 0xC00000:#02x}')
    return address


def build_room_address_table(rom):
    table = []
    for room_id in range(0xFF):
        rom.seek(snes_to_rom(0xDA8000) + (room_id * 3))
        ptr = rom.read(3)
        address = ptr[0] + (ptr[1] << 8) + (ptr[2] << 16)
        table.append({'id': room_id, 'address': snes_to_rom(address), 'compressed': is_compressed(rom, room_id)})

    sorted_table = sorted(table, key=lambda r: r['address'])

    for k in range(len(sorted_table) - 1):
        room = sorted_table[k]
        next_room = sorted_table[k + 1]
        if not room['compressed']:
            room['size'] = next_room['address'] - room['address']

    sorted_table[0xFE]['size'] = 0x1e22f3 - 0x1e22a0
    return sorted(sorted_table, key=lambda r: room['id'])


def output_dir(lang):
    return os.path.join(os.path.dirname(__file__), f'../text/{lang}/dialog')


def dump_rooms_for_lang(lang):
    table_path = os.path.join(os.path.dirname(__file__), '../text/table')

    table = Table(os.path.join(table_path, f'{lang}.tbl'))

    with open(os.path.join(os.path.dirname(__file__), f'../bl_{lang}.sfc'), 'rb') as rom_file:
        dump_rooms(rom_file, table, lang, output_dir=output_dir(lang))


if __name__ == '__main__':
    dump_rooms_for_lang('fr')
    dump_rooms_for_lang('en')
    # dump_rooms_for_lang('jp')
