import os
import struct
import freetype
import numpy
from PIL import Image
from script import Table


# def byte_to_bit_array(c):
#     retval = []
#     k = 8
#     for i in range(0, 8):
#         v = ((c & (1 << (k - i))) >> (k - i)) & 0xFF
#         retval.append(v)
#     return retval
from utils.dump_assets import byte_to_bit_array


def get_char(glyph):
    char = []
    letter = glyph.bitmap.buffer
    for k in range(0, len(letter) - 1):
        if k % 2:
            char.append(byte_to_bit_array(letter[k + 1] << 8 | letter[k]))

    for j in range(16 - len(char)):
        char.append([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    # metrics = glyph.metrics
    return char
    # 16px height,
    # empty_line =


if __name__ == "__main__":
    lang = "mz"
    table_path = os.path.join(os.path.dirname(__file__), "../text/table")
    table = Table(os.path.join(table_path, f"{lang}.tbl"))

    face = freetype.Face("helvetica-light-hint.ttf")
    # face = freetype.Face("Roboto-Thin-Hint.ttf")

    font = []
    for item in table.items:  # [('A', b'\x00'), ('g', b'\x01')]:
        face.set_char_size(16 * 72, 16 * 72)
        face.load_char(item[0], freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)

        bitmap = face.glyph.bitmap
        metrics = face.glyph.metrics

        # letter = bitmap.buffer
        # print('-' * 24)
        char_index = struct.unpack("B", item[1])[0]
        # print(f'{char_index:#02x}={item[0]}')
        char = get_char(face.glyph)
        char = numpy.vstack(char)
        font.append(char)

    font_array = numpy.array(font)
    h_stack = numpy.vstack(font)
    im = Image.fromarray(numpy.uint8(h_stack) * 255)

    with open("/tmp/helvetica.png", "wb") as fp:
        im.save(fp, format="PNG")

    print("end")
