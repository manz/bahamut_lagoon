"""
The battle banners' text, drawn into the banner graphics (utils/banner_gfx.py) at build time.

The tilemap holds the four banners one after the other, 32 rows each (PLAYER PHASE, ENEMY PHASE, PLAYER WIN, GAME
OVER). A banner is four bands of 8 rows: its big text on a band's first six rows, in the left half of the map on even
bands and the right half on odd ones (the game scrolls them in from both sides), then two rows of gradient. A small line
(ENEMY LOSE, YOU LOSE) sits on the row above each band's text: the previous band's last, or the banner's last above its
first band, as the game scrolls a banner's rows round.

The big letters are src_assets/banner_font.png, 8x48 cells in FONT_CHARS order, index 0 for the gradient behind them.
The small line is the staff credits' font (fonts/credits_font.bin.png) in colour 1 with a black shadow, as the game's.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt
from a816.writers import Writer
from PIL import Image

from utils.banner_gfx import Banner
from utils.cartridge import rom_offset

# The E9FD60 commands' long pointers to TILES, TILE_NUMBERS and FLIPS (06 00 E0 C6, 05 06 B2 EA C6, 07 F0 EC C6).
STREAM_POINTERS = (0xECFAF8, 0xECFAFD, 0xECFB01)
Pixels = npt.NDArray[np.uint8]  # colour indexes, rows by columns
Ink = npt.NDArray[np.bool_]
FONT = Path("src_assets/banner_font.png")
FONT_CHARS = "PLAYERHSNMWIGOVDUJCTFÉ"
SMALL_FONT = Path("fonts/credits_font.bin.png")
TILE = 8
COLUMNS = 32
ROWS = 128
BANDS = 4
BAND_ROWS = 8
HALF = COLUMNS // 2
GLYPH_HEIGHT = 48
MAX_TILES = 128  # E9FD60 uploads 0x1000 bytes of tiles
INK = 1
SHADOW = 7
TRANSPARENT = 0

# The colours behind the big text, row by row: the band's gradient, dark in the middle.
_TOP = (0xC, 0xC, 0xD, 0xD, 0xE, 0xE, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7)
TEXT_GRADIENT = _TOP + _TOP[::-1]
# The band's last two rows, the small line on the second.
GAP_GRADIENT = (0xB, 0xB, 0xA, 0xA, 9, 9, 8, 8, 8, 8, 9, 9, 0xA, 0xA, 0xB, 0xB)


@dataclass(frozen=True)
class BannerText:
    big: str
    column: int  # the big text's first tile in its half
    small: str = ""
    small_x: int = 0  # the small line's first pixel in its half


ENGLISH = (
    BannerText("PLAYER PHASE", 2),
    BannerText("ENEMY PHASE", 3),
    BannerText("PLAYER WIN", 4, "ENEMY LOSE", 32),
    BannerText("GAME OVER", 4, "YOU LOSE", 36),
)
FRENCH = (
    BannerText("PHASE DU JOUEUR", 1),
    BannerText("PHASE ENNEMIE", 2),
    BannerText("VICTOIRE", 4, "ENNEMI VAINCU", 16),
    BannerText("DÉFAITE", 5, "VOUS AVEZ PERDU", 8),
)


def read_font(path: Path = FONT) -> dict[str, Pixels]:
    sheet = np.array(Image.open(path))
    return {char: sheet[:, k * TILE : (k + 1) * TILE] for k, char in enumerate(FONT_CHARS)}


def read_small_font(path: Path = SMALL_FONT) -> dict[str, Ink]:
    """The credits font's capitals: A-O on its first row of cells from the second cell, P-Z on its third row."""
    ink = np.array(Image.open(path).convert("L")) > 0
    font = {}
    for k, char in enumerate("ABCDEFGHIJKLMNO"):
        font[char] = ink[:TILE, (k + 1) * TILE : (k + 2) * TILE]
    for k, char in enumerate("PQRSTUVWXYZ"):
        font[char] = ink[2 * TILE : 3 * TILE, k * TILE : (k + 1) * TILE]
    return font


def compose(texts: tuple[BannerText, ...], font: dict[str, Pixels], small_font: dict[str, Ink]) -> Pixels:
    """The whole tilemap's pixels, colour indexes, ROWS * 8 by COLUMNS * 8."""
    image = np.zeros((ROWS * TILE, COLUMNS * TILE), np.uint8)
    band = np.array(TEXT_GRADIENT + GAP_GRADIENT, np.uint8)
    image[:] = np.tile(band, ROWS // BAND_ROWS)[:, None]
    banner_rows = BANDS * BAND_ROWS
    for number, text in enumerate(texts):
        for band_number in range(BANDS):
            band_row = band_number * BAND_ROWS
            top = (number * banner_rows + band_row) * TILE
            left = HALF * TILE * (band_number % 2)
            _draw_big(image[top : top + GLYPH_HEIGHT], left + text.column * TILE, text.big, font)
            if text.small:
                above = (number * banner_rows + (band_row - 1) % banner_rows) * TILE
                _draw_small(image[above : above + TILE], left + text.small_x, text.small, small_font)
    return image


def _draw_big(rows: Pixels, x: int, text: str, font: dict[str, Pixels]) -> None:
    for char in text:
        if char != " ":
            glyph = font[char]
            cell = rows[:, x : x + TILE]
            cell[glyph != TRANSPARENT] = glyph[glyph != TRANSPARENT]
        x += TILE


def _draw_small(rows: Pixels, x: int, text: str, font: dict[str, Ink]) -> None:
    ink = np.zeros((TILE, len(text) * TILE), bool)
    for k, char in enumerate(text):
        if char != " ":
            ink[:, k * TILE : (k + 1) * TILE] = font[char]
    shadow = np.zeros_like(ink)
    shadow[1:, 1:] = ink[:-1, :-1]
    area = rows[:, x : x + ink.shape[1]]
    area[shadow & ~ink] = SHADOW
    area[ink] = INK


def tiles_of(image: Pixels) -> Banner:
    """The tiles, tile numbers and flips that draw `image`, each distinct tile once, flipped copies included."""
    tiles: list[bytes] = []
    known: dict[bytes, tuple[int, int]] = {}
    numbers = bytearray()
    flips = bytearray()
    for row in range(ROWS):
        for column in range(COLUMNS):
            pixels = image[row * TILE : (row + 1) * TILE, column * TILE : (column + 1) * TILE]
            key = pixels.tobytes()
            if key not in known:
                number = len(tiles)
                tiles.append(_planar(pixels))
                for flip in (3, 2, 1, 0):
                    known[_flipped(pixels, flip).tobytes()] = (number, flip)
            number, flip = known[key]
            numbers.append(number)
            flips.append(flip)
    if len(tiles) > MAX_TILES:
        raise ValueError(f"the banners take {len(tiles)} tiles, the game uploads {MAX_TILES}")
    return Banner(b"".join(tiles), bytes(numbers), bytes(flips))


def _flipped(pixels: Pixels, flip: int) -> Pixels:
    """`pixels` under a tilemap flip field: 1 flips horizontally, 2 vertically."""
    if flip & 1:
        pixels = pixels[:, ::-1]
    if flip & 2:
        pixels = pixels[::-1, :]
    return pixels


def _planar(pixels: Pixels) -> bytes:
    """An 8x8 tile of colour indexes as a 4bpp SNES tile."""
    planes = [np.packbits((pixels >> plane) & 1, axis=1)[:, 0] for plane in range(4)]
    low = np.stack([planes[0], planes[1]], axis=1).tobytes()
    high = np.stack([planes[2], planes[3]], axis=1).tobytes()
    return low + high


def pixels_of(banner: Banner) -> Pixels:
    """What `banner`'s tilemap draws, as compose() returns it."""
    image = np.zeros((ROWS * TILE, COLUMNS * TILE), np.uint8)
    for entry, (number, flip) in enumerate(zip(banner.tile_numbers, banner.flips, strict=True)):
        row, column = divmod(entry, COLUMNS)
        tile = banner.tiles[number * 32 : (number + 1) * 32]
        planes = np.frombuffer(tile, np.uint8)
        bits = [np.unpackbits(planes[offset::2][:TILE, None], axis=1) for offset in (0, 1)]
        bits += [np.unpackbits(planes[16 + offset :: 2][:TILE, None], axis=1) for offset in (0, 1)]
        pixels = np.zeros((TILE, TILE), np.uint8)
        for plane, bit in enumerate(bits):
            pixels |= bit << plane
        image[row * TILE : (row + 1) * TILE, column * TILE : (column + 1) * TILE] = _flipped(pixels, flip)
    return image


def french_banner() -> Banner:
    return tiles_of(compose(FRENCH, read_font(), read_small_font()))


def insert_banner(writer: Writer, address: int) -> int:
    """Write the French banner's streams from `address` and point the E9FD60 commands at them; return the address past
    them."""
    for stream, pointer in zip(french_banner().streams(), STREAM_POINTERS, strict=True):
        end = address + len(stream)
        if address >> 16 != (end - 1) >> 16:
            raise ValueError(f"a banner stream at {address:#08x} would cross its bank")
        writer.write_block(stream, rom_offset(address))
        writer.write_block(address.to_bytes(3, "little"), rom_offset(pointer))
        address = end
    return address
