from io import BytesIO

import numpy as np
from PIL import Image


def byte_to_bit_array(c):
    retval = []
    k = 16
    for i in range(16):
        v = ((c & (1 << (k - i))) >> (k - i)) & 0xFF
        retval.append(v)
    return retval


def bytes_to_char(char_data):
    data = []
    k = 0
    # for z in range(2):
    #     data.append([0] * 16)
    #
    while k < len(char_data) - 1:
        d = char_data[k]
        c = char_data[k + 1]
        expanded_char = byte_to_bit_array(c | (d << 8))
        data.append(expanded_char)

        k += 2

    # for z in range(2):
    #     data.append([0] * 16)
    #
    return data


def dump_vwf(data):
    font = None
    for i in range(64):
        line = None
        for k in range(16):
            char_index = i * 16 + k

            char_data = data[char_index * 24 : (char_index + 1) * 24]
            char = bytes_to_char(char_data)

            if line is not None:
                line = np.concatenate([line, char], 1)
            else:
                line = char
        if font is not None:
            font = np.concatenate([font, line], 0)
        else:
            font = line

    im = Image.fromarray(np.uint8(font * 255))
    bio = BytesIO()

    im.save(bio, "PNG")
    return bio.getvalue()


asset_processor = {"vwf": dump_vwf, "raw": lambda data: data}


def dump_asset(asset_type, rom, address, size, output_file):
    with open(output_file, "wb") as output:
        rom.seek(address)
        data = rom.read(size)
        # extract_font(data)
        # print(extract_font(data))
        image_data = asset_processor[asset_type](data)
        output.write(image_data)


def process_asset_list(rom, assets):
    for asset in assets:
        args = (rom,) + asset[1:]
        dump_asset(asset[0], *args)


if __name__ == "__main__":
    # assets_to_dump = [
    #     ('vwf', 0x2D0000, 0x6000, 'src_assets/vwf.png'),
    #     ('raw', 0x8A000, 0xD00, 'src_assets/8x8_font.dat'),
    #     ('raw', 0x261B40, 0x264940 - 0x261B40, 'src_assets/8x8_battle.dat'),
    #     # (0x28CD55, 0x400, 'src_assets/intro_font.dat')
    # ]
    #
    # with open('bl.sfc', 'rb') as rom:
    #     process_asset_list(rom, assets_to_dump)
    #

    pass
