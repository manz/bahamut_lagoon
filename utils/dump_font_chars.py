import numpy as np
import tesserocr
from PIL import Image

from utils.dump_assets import bytes_to_char


def get_char_from_image(image):
    resized_image = image.resize((image.width * 5, image.width * 5), Image.LANCZOS)
    return tesserocr.image_to_text(resized_image, lang="jpn", psm=10)


def dump_font_chars(data):
    k = 0
    max_k = 1024
    char_height = 16
    ch = 12 * 2
    font = []
    print("laa")
    while k < max_k:
        char_data = data[k * ch : (k + 1) * ch]
        expanded_data = bytes_to_char(char_data)
        image = Image.fromarray(np.uint8(expanded_data) * 255)
        print(f"{k:x}")
        print(get_char_from_image(image))
        k += 1


if __name__ == "__main__":
    with open("../bl.sfc", "rb") as rom:
        rom.seek(0x2D0000)
        data = rom.read(0x6000)
        dump_font_chars(data)
