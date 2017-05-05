import struct
import os
import math
import re

from a816.cpu.cpu_65c816 import snes_to_rom, rom_to_snes, RomType
from a816.writers import IPSWriter

from utils.disasm import live_disasm
from utils.lz import lz_decompress, lz_compress
from utils.vm.opcodes_map import opcode_table, opcode_names
from utils.vm.room import Room

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
    room_id_high = math_pow_2(room_id & 0x07)
    room_id_low = room_id >> 3

    rom.seek(snes_to_rom(0xDA8300) + room_id_low)
    return (struct.unpack('B', rom.read(1))[0] & room_id_high) != 0


def get_compressed_room(rom, room_id, version):
    """used for rebuild script"""
    rom.seek(snes_to_rom(0xDA8000) + (room_id * 3))
    ptr = rom.read(3)

    rom.seek(snes_to_rom(ptr[0] + (ptr[1] << 8) + (ptr[2] << 16)))

    decompressed = decompress_block(rom)
    room = Room(decompressed, opcode_table, opcode_names, version)
    room.id = room_id
    # room = live_disasm(room_id, decompressed, version)
    return room


def dump_room(rom, room_id, address, compressed=False, size=None, version=''):
    rom.seek(address)
    print(f'room: {room_id}')
    if compressed:
        decompressed = decompress_block(rom)
        # Might be not necessary but for completion it is implemented
        # (results in mostly very short rooms)
        # else:
        #     decompressed = rom.read(size)
        room = live_disasm(room_id, decompressed, version)
        texts = room.dump_text()
        if texts:
            with open('../rooms{}/{:04d}.xml'.format(version, room_id), 'wt', encoding='utf-8') as output:
                output.write(texts)
            # updated_room = room.update_text(f'../rooms{version}/{room_id:04d}.xml')
            # with open(f'../seekndestroy/{room_id:04d}.bin', 'wb') as output:
            #     compressed = compress_room(updated_room)
            #     output.write(compressed)


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


DANGER = [250]


def dump_rooms(rom, version=''):
    room_table = build_room_address_table(rom)
    for room in sorted(room_table, key=lambda r: r['id']):
        if room['id'] not in DANGER:
            dump_room(rom, room['id'], room['address'],
                      compressed=room['compressed'],
                      size=room.get('size'), version=version)


def build_text_patch(rom, writer, version=''):
    xmlfile_re = re.compile('(\d+)\.xml')
    files = os.listdir(os.path.join('rooms_mz'))
    address = snes_to_rom(0xF00000)

    for file in files:
        match = xmlfile_re.match(file)
        if match:
            room_id = int(match.group(1))
            if is_compressed(rom, room_id):
                # print('-' * 80)
                # print('room_id', room_id)
                room = get_compressed_room(rom, room_id, version)
                # print('addr', hex(address))
                updated_room = room.update_text(f'rooms_mz/{room_id:04d}.xml')
                # print('uncompressed len', hex(len(updated_room)))
                compressed = compress_room(updated_room)

                writer.write_block(compressed, address)
                value = rom_to_snes(address, RomType.high_rom)

                writer.write_block(struct.pack('<HB', value & 0xFFFF, (value >> 16) & 0xFF),
                                   snes_to_rom(0xDA8000) + (room_id * 3))
                # print('len', hex(len(compressed)))
                # print('ratio {}'.format((len(compressed) / len(updated_room)) * 100))
                address += len(compressed) + 1


#
# def dump_intro_room(rom):
#     rom.seek(snes_to_rom(0xDA8000) + (0xFE * 3))
#     ptr = rom.read(3)
#     room_address = ptr[0] + (ptr[1] << 8) + (ptr[2] << 16)
#     dump_room(rom, 0xFE, room_address)


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


def build_dialog_text_patch():
    with open('../bl.sfc', 'rb') as rom_file:
        with open('bl_fr_text.ips', 'wb') as ips_file:
            writer = IPSWriter(ips_file)
            writer.begin()
            # dump_rooms(rom_file, version='_en')
            build_text_patch(rom_file, writer, version='_en')

            writer.end()


if __name__ == '__main__':
    #build_dialog_text_patch()
    with open('../bl.sfc', 'rb') as rom_file:
        dump_rooms(rom_file, version='_jp')

    # with open('../ble_snes.sfc', 'rb') as rom_file:
    #     dump_rooms(rom_file, version='_en')




    # 0x1b)
    # dump_room(rom_file, 0xFE, 0x1e22a0+0xC00000, 0x1e22f3 - 0x1e22a0)
    # dump_room(rom_file, 0xFA, 0x1e22a0+0xC00000, 0x1e22f3 - 0x1e22a0)

    # dump_intro_room(rom_file)
