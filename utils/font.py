#!/usr/bin/env python

import os
import numpy as np
from PIL import Image


def get_char(image, char, char_width, char_height):
    shape = image.shape
    width = shape[1]
    height = shape[0]

    x_char_count = width / char_width
    y_char_count = height / char_height

    line = int(char / x_char_count)
    column = int(char % x_char_count)

    x_offset = column * char_width
    y_offset = line * char_height

    return image[y_offset:y_offset + char_height, x_offset:x_offset + char_width]


def char_as_1bbp(char):
    binary_data = []
    for byte in char:
        byte_value = int(''.join(byte.astype(str)).ljust(8, '0'), 2)
        binary_data.append(byte_value)
    return bytes(binary_data)


def get_max_width(char):
    max_width = 0
    for byte in char:
        trimmed = np.trim_zeros(byte, 'b')
        max_width = max(len(trimmed), max_width)

    return max_width


def convert_font(font_file, empty_chars=None):
    image = np.array(Image.open(font_file))
    empty_chars = empty_chars or {}

    char = get_char(image, 0, 8, 16)

    data = b''
    char_index = 0
    while len(char) > 0:
        char = get_char(image, char_index, 8, 16)
        data += char_as_1bbp(char)

        if char_index in empty_chars:
            max_width = empty_chars[char_index]
            print(f'{char_index:#02x}={max_width:#02x}')
            data += bytes([max_width])
        else:
            max_width = get_max_width(get_char(image, char_index, 8, 16))
            print(f'{char_index:#02x}={max_width:#02x}')
            data += bytes([max_width])

        char_index += 1

    return data


def print_length_table(data):
    for k in range(0xFF):
        print(f'{k:#02x} = {data[k * 17 + 16]:d}')


char_length_override = {
    0xef: 4,
    0xa3: 5,  # ,
    0xd5: 7,
    0xd6: 4,
    0xd7: 7,
    0xd8: 6,

    # 0x88: 6,  # :
    # 0xef: 2,  # original space
    # 0x26: 2  # another space
}

if __name__ == '__main__':
    this_dir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(this_dir, '../', 'assets/vwf.bin'), 'wb') as binary_asset:
        data = convert_font('fonts/fft.png', empty_chars=char_length_override)
        binary_asset.write(data)
