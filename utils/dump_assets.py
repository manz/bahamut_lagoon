from collections.abc import Callable
from pathlib import Path
from typing import BinaryIO

import numpy as np
from katsuji import png


def byte_to_bit_array(c: int) -> list[int]:
    retval = []
    k = 16
    for i in range(16):
        v = ((c & (1 << (k - i))) >> (k - i)) & 0xFF
        retval.append(v)
    return retval


def bytes_to_char(char_data: bytes) -> list[list[int]]:
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


def dump_vwf(data: bytes, output_file: str) -> None:
    lines = []
    for i in range(64):
        chars = []
        for k in range(16):
            char_index = i * 16 + k

            char_data = data[char_index * 24 : (char_index + 1) * 24]
            chars.append(bytes_to_char(char_data))
        lines.append(np.concatenate(chars, 1))
    font = np.concatenate(lines, 0)

    png.write(Path(output_file), (font * 255).astype(np.uint8))


def dump_raw(data: bytes, output_file: str) -> None:
    Path(output_file).write_bytes(data)


asset_processor: dict[str, Callable[[bytes, str], None]] = {"vwf": dump_vwf, "raw": dump_raw}


def dump_asset(asset_type: str, rom: BinaryIO, address: int, size: int, output_file: str) -> None:
    rom.seek(address)
    asset_processor[asset_type](rom.read(size), output_file)


def process_asset_list(rom: BinaryIO, assets: list[tuple[str, int, int, str]]) -> None:
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
