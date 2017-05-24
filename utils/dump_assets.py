import math
import numpy as np
import struct

import os
from PIL import Image
from io import BytesIO


def byte_to_bit_array(c):
    retval = []
    k = 16
    for i in range(0, 16):
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


def extract_font_char_for_ocr(data):
    k = 0
    max_k = 1024
    char_height = 16
    ch = 12 * 2
    font = []
    print('laa')
    while k < max_k:  # len(data[k * ch: (k + 1) * ch]) == ch:
        char_data = data[k * ch: (k + 1) * ch]
        expanded_data = bytes_to_char(char_data)
        image = Image.fromarray(np.uint8(expanded_data) * 255)
        with open(f'./text/ocr/{k:04d}.png', 'wb') as png_char:
            image.save(png_char, format='PNG')

        font.append(expanded_data)
        k += 1

    # print('kiki', k)
    # font_a = np.array(font)  # k, 12, 12
    # for lines in range(0, max_k//16):

    # stacked = np.hstack(font_a[i, :, :] for i in range(max_k))
    # stacked = font_a
    # image = Image.fromarray(np.uint8(stacked))
    # with open('/tmp/font.png', 'wb') as png_char:
    #     image.save(png_char, format='PNG')

    return np.array(font)


def dump_vwf(data):
    font = None
    for i in range(0, 64):
        line = None
        for k in range(0, 16):
            char_index = i * 16 + k

            char_data = data[char_index * 24: (char_index + 1) * 24]
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

    im.save(bio, 'PNG')
    return bio.getvalue()


def read_tesseract_results():
    with open('./text/index.html', 'w', encoding='utf-8') as out:
        out.write('<html>')
        out.write('<head> <meta charset="UTF-8"></head>')
        out.write('<body>')
        out.write(
            '''<style>
            body {
            font-family: "HiraKakuPro-W3", "Hiragino Kaku Gothic Pro W3", "Hiragino Kaku Gothic Pro", "ヒラギノ角ゴ Pro W3", "メイリオ", Meiryo, "游ゴシック", YuGothic, "ＭＳ Ｐゴシック", "MS PGothic", "ＭＳ ゴシック", "MS Gothic", sans-serif;
            }
            </style>''')
        out.write('<table style="font-size:2em">')
        # ok_k = 160
        for k in range(1024):
            with open(f'./text/ocr/scaled/{k:04d}.txt', 'rt', encoding='utf-8') as t:
                # print('{:04x}={}'.format(k, t.read().strip()))
                # if k <= ok_k:
                out.write('<tr style="background-color:green">')
                out.write(f'<td>{k:04d}</td>')
                out.write(f'<td><img width=50 src="./ocr/scaled/{k:04d}.jpg"></img></td>')
                out.write(f'<td>{t.read().strip()}</td>')
                out.write('</tr>')

                # else:
                #     out.write(
                #         '<tr><td>{:04d}</td><td><img src="./ocr/{:04d}.png"></img></td><td>{}</td></tr>'.format(
                #             k,
                #             k,
                #             t.read().strip()))
        out.write('</table>')
        out.write('</body>')
        out.write('</html>')


def put_tesseract_results_in_firebase():
    for k in range(1024):
        with open(f'./text/ocr/scaled/{k:04d}.txt', 'rt', encoding='utf-8') as t:
            value = t.read().strip()


def build_table():
    with open('./text/table_jp.tbl', 'w', encoding='utf-8') as output:
        for k in range(1024):
            with open(f'./text/ocr/scaled/{k:04d}.txt', encoding='utf-8') as t:
                value = t.read().strip()
                if value:
                    code_point = k + 0xF000
                    output.write(f'{code_point:04x}={value}\n')
        output.write('F0EF= \n')
        output.write('F0FE=\\n\n')
        output.write('F0FD=[end1]\n')
        output.write('F0FF=[end]\n')


def batch_rename():
    for k in range(1024):
        os.rename(f'/tmp/jap_text/{k:04x}.txt', f'/tmp/jap_text/{k:04d}.txt')
        os.rename(f'/tmp/jap_text/{k:04x}.png', f'/tmp/jap_text/{k:04d}.png')


asset_processor = {
    'vwf': dump_vwf,
    'raw': lambda data: data
}


def dump_asset(asset_type, rom, address, size, output_file):
    with open(output_file, 'wb') as output:
        rom.seek(address)
        data = rom.read(size)
        # extract_font(data)
        # print(extract_font(data))
        image_data = asset_processor[asset_type](data)
        # extract_font_char_for_ocr(data)
        output.write(image_data)


def process_asset_list(rom, assets):
    for asset in assets:
        args = (rom,) + asset[1:]
        dump_asset(asset[0], *args)


if __name__ == '__main__':
    # batch_rename()
    # read_tesseract_results()
    # build_table()
    # exit(1)
    # build_table()
    assets_to_dump = [
        ('vwf', 0x2D0000, 0x6000, 'src_assets/vwf.png'),
        ('raw', 0x8A000, 0xD00, 'src_assets/8x8_font.dat'),
        ('raw', 0x261B40, 0x264940 - 0x261B40, 'src_assets/8x8_battle.dat'),
        # (0x28CD55, 0x400, 'src_assets/intro_font.dat')
    ]

    with open('bl.sfc', 'rb') as rom:
        process_asset_list(rom, assets_to_dump)
#
