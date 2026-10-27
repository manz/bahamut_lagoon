"""
Seed the dialogue font: fonts/dialog.png from far_fast_of_eden_zero's 8x16 VWF font (ff4's, with star_ocean's,
treasure_hunter_g's and its own additions), remapped by text onto text/table/mz.tbl with katsuji's `remap`.

One-off: the png is the source afterwards (edit it, katsuji builds it). Cells the remap leaves blank keep fft.png's:
the cells no table text names (the ✚ and ⏱ icons, D5-D8). The `` and '' pair is drawn as « »; Û is drawn here, U with
Ê's circumflex.

    uv run python -m utils.seed_dialog_font
"""

from pathlib import Path

import numpy as np
import numpy.typing as npt
from katsuji.atlas import Atlas
from katsuji.remap import remap, table_codes
from PIL import Image

CELL_W, CELL_H, COLS = 8, 16, 16
SOURCE = Path.home() / "Projects/far_fast_of_eden_zero"
SOURCE_PNG = SOURCE / "fonts/tmz_dialog.png"
SOURCE_TABLE = SOURCE / "text/tmz_fr.tbl"
TABLE = Path("text/table/mz.tbl")
FFT = Path("fonts/fft.png")
PNG = Path("fonts/dialog.png")
ALIASES = {"``": "«", "''": "»"}  # mz.tbl's texts for the guillemets
CIRCUMFLEX = ["..##..", ".#..#."]  # rows 1-2, over a 6-pixel capital


Span = slice[int, int, None]


def cell(code: int) -> tuple[Span, Span]:
    row, col = divmod(code, COLS)
    return np.s_[row * CELL_H : (row + 1) * CELL_H, col * CELL_W : (col + 1) * CELL_W]


def seed() -> npt.NDArray[np.uint8]:
    """The palette indices of every cell: fft.png's, with each text the source draws in the source's glyph."""
    target = table_codes(TABLE)
    source = table_codes(SOURCE_TABLE)
    for text, alias in ALIASES.items():
        source[text] = source[alias]
    layer = remap(Atlas.open(SOURCE_PNG, CELL_W, CELL_H), source, target).pixels != 0
    pixels = np.array(Image.open(FFT), dtype=np.uint8)
    for code in target.values():
        if layer[cell(code)].any():
            pixels[cell(code)] = layer[cell(code)]
    u_circumflex = layer[cell(target["U"])].astype(np.uint8)
    for y, row in enumerate(CIRCUMFLEX, start=1):
        u_circumflex[y, : len(row)] = [pixel == "#" for pixel in row]
    pixels[cell(target["Û"])] = u_circumflex
    return pixels


def main() -> None:
    with Image.open(FFT) as fft:
        palette = fft.getpalette()
    image = Image.fromarray(seed(), mode="P")
    image.putpalette(palette or [])
    image.save(PNG)
    print(PNG)


if __name__ == "__main__":
    main()
