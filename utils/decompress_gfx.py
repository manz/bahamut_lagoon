import struct
from a816.cpu.cpu_65c816 import snes_to_rom
from io import BytesIO

from utils.lz import lz_decompress, lz_compress, find_back_reference


def compress_asset(data):
    compressed = bytearray()
    k = 0
    while k < len(data):
        back_reference = find_back_reference(data,
                                             k,
                                             search_patterns=True,
                                             buffer_size=0x7ff,
                                             max_length=0x3f,
                                             min_length=3)
        if back_reference:
            reference, length = back_reference
            # data_2    data_1
            # aaaa aaaa | aa ll llll

            if reference > 0x3ff:
                compressed += b'\x1b'
            else:
                compressed += b'\x1a'

            # reference = k - reference

            a = reference & 0xFF
            b = ((reference & 0x300) >> 2) | length

            compressed.append(b)
            compressed.append(a)

            k += length
        else:
            # put byte in compressed stream
            if data[k] in [0x1a, 0x1b]:
                compressed += struct.pack('B', data[k]) + b'\x00\x00'
            else:
                compressed.append(data[k])
            k += 1

    compressed += b'\x1a\x00\x01'
    return b'\x01' + compressed


def decompress_asset(rom_file):
    decompressed = bytearray()
    # skip_first_byte
    _ = rom_file.read(1)
    pos = rom_file.tell()
    while True:
        current_pos = rom_file.tell() - pos

        control_byte = rom_file.read(1)[0]

        if control_byte in [0x1a, 0x1b]:
            data_1 = rom_file.read(1)[0]
            data_2 = rom_file.read(1)[0]
            word = (data_2 << 8) | data_1

            # end of data stream XX 00 01
            if word == 0x0100:
                break

            # Control codes 1A 1B needs to be escaped XX 00 00
            if word == 0x0000:
                decompressed += bytes([control_byte])
            else:
                # data_2    data_1
                # aaaa aaaa aa ll llll
                # low       hi   len
                length = data_1 & 0x3f
                pointer = (data_2 & 0xff) | ((data_1 & 0xc0) << 2)

                if control_byte == 0x1b:
                    pointer |= 0x400

                back_pointer = len(decompressed) - pointer

                for l in range(0, length):
                    decompressed += bytes([decompressed[back_pointer + l]])
        else:
            decompressed += bytes([control_byte])
    return decompressed


decompress_gfx_xrefs = [
    0xee7d46, 0xee850b, 0xee8548, 0xee855d, 0xee8572, 0xee8593,
    0xeed8a3, 0xeed8b0, 0xeed8bd,
    0xee850b]

lz_compressed_gfxs = [
    0xcc2d80,
    0xe87432,
    0xe883ec,
    0xe89a4f
]


def lz_decompress_gfx(rom):
    size = struct.unpack('<H', rom_file.read(2))[0]
    # print(f'size {size:#0{6}x}')
    data = rom_file.read(size)
    decompressed = lz_decompress(data)

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

            decompressed = lz_decompress(data, decompressed)
        else:
            break
    # print(f'end {rom.tell():#x}')
    return decompressed


def lz_compress_gfx(data):
    compressed_data = lz_compress(data, search_patterns=False)
    compressed_length = len(compressed_data)
    return struct.pack('<H', compressed_length) + compressed_data + b'\x00'


if __name__ == '__main__':
    with open('../bl.sfc', 'rb') as rom_file:
        for decompress_gfx_xref in decompress_gfx_xrefs:
            rom_file.seek(snes_to_rom(decompress_gfx_xref + 4))
            low = struct.unpack('<H', rom_file.read(2))[0]
            high = struct.unpack('>H', rom_file.read(2))[0]

            address = low | (high << 8)
            rom_file.seek(snes_to_rom(address))
            print(f'address = {address:#06x}')
            with open(f'/tmp/{address:06x}.bin', 'wb') as f:
                f.write(decompress_asset(rom_file))
