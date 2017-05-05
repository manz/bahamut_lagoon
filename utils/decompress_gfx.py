import struct
from a816.cpu.cpu_65c816 import snes_to_rom


def decompress_asset(rom_file):
    decompressed = bytearray()
    # skip_first_byte
    _ = rom_file.read(1)
    pos = rom_file.tell()
    print(f'{pos + 0xC00000:#06x}')

    while True:
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


decompress_gfx_xrefs = [0xee7d46, 0xee850b, 0xee8548, 0xee855d, 0xee8572, 0xee8593,
                        0xeed8a3, 0xeed8b0, 0xeed8bd]

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
