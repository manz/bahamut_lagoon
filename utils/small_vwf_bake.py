"""
small_vwf's tiles for every fixed name, rendered at build time.

render() is src/small_vwf.s in Python, step for step: the same glyph records, pen and shadow, so a name rendered
without kerning is byte for byte what the game would compose. The game copies a baked name's tiles instead of drawing
its glyphs and shading them; only names it reads from RAM (the party's) still render there. A baked string is also
kerned with the font's pair table (katsuji's collision-fitted kerning-candidates), which the game's renderer skips.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

MAX_CELLS = 12  # SMALL_VWF_MAX_CELLS
MAX_CHARS = 24  # SMALL_VWF_MAX_CHARS
SHADOW_GAP = 1
GLYPH = 9  # small_font.dat: 8 rows of 1bpp, then the advance width
GLYPHS = 256
KERNING_PAIR = 3  # small_font.dat after the glyphs: a word count, then (left, right, pixels tighter) per pair
TILE = 16  # a 2bpp tile
BANK = 0x10000
FONT = Path("assets/small_font.dat")


def kerning(font: bytes) -> dict[tuple[int, int], int]:
    """small_font.dat's pair table: pixels to take off the advance between two codes."""
    table = GLYPHS * GLYPH
    count = int.from_bytes(font[table : table + 2], "little")
    pairs = font[table + 2 : table + 2 + count * KERNING_PAIR]
    return {(pairs[i], pairs[i + 1]): pairs[i + 2] for i in range(0, len(pairs), KERNING_PAIR)}


def render(
    font: bytes, codes: bytes, max_cells: int = MAX_CELLS, pairs: Mapping[tuple[int, int], int] | None = None
) -> tuple[bytes, int]:
    """The 2bpp tiles of `codes` (MAX_CELLS cells, clear past the last it reaches) and how many cells it reaches,
    kerned with `pairs` when given."""
    ink = bytearray((MAX_CELLS + 1) * 8)
    pen = 0
    previous = None
    for code in codes[:MAX_CHARS]:
        if code >= 0xFE:
            break
        at = pen - (pairs or {}).get((previous, code), 0) if previous is not None else pen
        cell = at >> 3
        if cell >= max_cells:
            break  # dropped, and every glyph after it: a kerned pair must not pull one back in
        pen = at
        previous = code
        glyph = font[code * GLYPH : (code + 1) * GLYPH]
        for row in range(8):
            shifted = glyph[row] << 8 >> (pen & 7)
            ink[cell * 8 + row] |= shifted >> 8
            ink[cell * 8 + 8 + row] |= shifted & 0xFF
        pen += glyph[8] + SHADOW_GAP
    cells = min((pen + 8) >> 3, max_cells)
    tiles = bytearray(MAX_CELLS * TILE)
    for byte in range(cells * 8):
        shadow = ink[byte] >> 1
        if byte >= 8:
            shadow |= (ink[byte - 8] & 1) << 7  # the left cell's last column
        if byte & 7:
            shadow |= ink[byte - 1]  # the row above
        shadow &= ~ink[byte] & 0xFF
        tiles[byte * 2] = ink[byte] | shadow
        tiles[byte * 2 + 1] = shadow
    return bytes(tiles), cells


@dataclass(frozen=True)
class Baked:
    offset: int  # into the blob
    cells: int


def bake(font: bytes, names: list[bytes], blob: bytearray, offsets: dict[bytes, int]) -> list[Baked]:
    """Append each name's tiles to `blob`, once for identical tiles (`offsets` remembers them across calls); their
    entries. The blob must stay within a bank: the game reads it with one block move. Names are kerned with the
    font's pair table."""
    pairs = kerning(font)
    entries = []
    for codes in names:
        tiles, cells = render(font, codes, pairs=pairs)
        tiles = tiles[: cells * TILE]
        if tiles not in offsets:
            offsets[tiles] = len(blob)
            blob.extend(tiles)
        entries.append(Baked(offsets[tiles], cells))
    if len(blob) > BANK:
        raise ValueError(f"baked names take {len(blob)} bytes, more than a bank")
    return entries
