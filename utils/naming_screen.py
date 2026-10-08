"""
The naming screen's three character pages, laid out for French names.

Each page is a 32x32 BG3 tilemap the screen decompresses into 7E:C400 (`EE3B40`, sources at EE0FA4, EE0E52 and
EE0D58, picked by the page in $C0). The grid has two blocks of 5 columns (map columns 7-15 and 18-26, even ones) by
10 rows (map rows 6-24, even ones). Pressing A types the tile code under the cursor (`EEDB3C`): E1 types a space,
and a dakuten (31) or handakuten (32) tile on the row above turns a kana into its voiced form.

The codes are the text codes both fonts draw: the 8x8 menu font for menus and the dialogue font for dialog, so a
typed name reads the same in both. Neither has accented capitals the other draws, and the dialogue font has no
( ) /: the grids leave them out. The pages keep their places and their labels' cells (Hira, Kata, Autre).

The tilemaps are packed in the format `EE1D00` reads: a skipped first byte; 1A or 1B then a word escapes, 0000
standing for the escape byte itself, 0100 ending the stream, anything else copying `lo & 0x3F` bytes (0 = 256)
from `(escape & 1) << 10 | (lo & 0xC0) << 2 | hi` bytes back.
"""

from collections.abc import Sequence
from pathlib import Path

from katsuji.formats import VwfFont
from script import Table

from utils.cartridge import rom_offset

PAGES = (0xEE0FA4, 0xEE0E52, 0xEE0D58)  # Hira, Kata, Autre
SOURCE_OPERANDS = (0xEED8A7, 0xEED8B4, 0xEED8C1)  # the 24-bit source after each `jsl EE3B40`
MAP_SIZE = 0x800
COLUMNS = 32
GRID_ROWS = range(6, 26, 2)
LEFT_COLUMNS = range(7, 16, 2)
RIGHT_COLUMNS = range(18, 27, 2)
SPACE_TILE = 0xE1  # types a space
EDIT_ROW = 20  # the right block's row of edit keys: dash, comma, space
ESCAPES = (0x1A, 0x1B)
END = (0x00, 0x01)
MAX_DISTANCE = 0x7FF
MAX_LENGTH = 0x3F
MIN_MATCH = 4  # a back-reference costs 3 bytes

EDIT_KEYS = "-,"
UPPER = ["ABCDE", "FGHIJ", "KLMNO", "PQRST", "UVWXY", "Z"]
LOWER = ["abcde", "fghij", "klmno", "pqrst", "uvwxy", "z"]
DIGITS = ["12345", "67890"]
ACCENTS = ["éèêëà", "âçîïô", "ûù"]
PUNCTUATION = ["-.,'!", "?"]
LAYOUT = (
    (UPPER, DIGITS),  # Hira: capitals
    (LOWER, ACCENTS),  # Kata: lower case
    (PUNCTUATION, []),  # Autre
)


def decode(rom: bytes, offset: int) -> bytes:
    x = offset + 1
    out = bytearray()
    while True:
        code = rom[x]
        if code not in ESCAPES:
            out.append(code)
            x += 1
            continue
        low, high = rom[x + 1], rom[x + 2]
        x += 3
        if (low, high) == (0, 0):
            out.append(code)
        elif (low, high) == END:
            return bytes(out)
        else:
            distance = (code & 1) << 10 | (low & 0xC0) << 2 | high
            for _ in range((low & 0x3F) or 256):
                out.append(out[len(out) - distance])


def encode(data: bytes) -> bytes:
    """Greedy: the longest earlier match of at least MIN_MATCH bytes, else a literal."""
    out = bytearray([0x00])
    position = 0
    while position < len(data):
        best_length, best_distance = 0, 0
        for distance in range(1, min(position, MAX_DISTANCE) + 1):
            length = 0
            while (
                length < MAX_LENGTH
                and position + length < len(data)
                and data[position + length - distance] == data[position + length]
            ):
                length += 1
            if length > best_length:
                best_length, best_distance = length, distance
        if best_length >= MIN_MATCH:
            out += bytes(
                [
                    ESCAPES[best_distance >> 10],
                    (best_distance >> 2) & 0xC0 | best_length,
                    best_distance & 0xFF,
                ]
            )
            position += best_length
        else:
            code = data[position]
            out += bytes([code, 0, 0]) if code in ESCAPES else bytes([code])
            position += 1
    return bytes(out + bytes([ESCAPES[0], *END]))


def _cell(column: int, row: int) -> int:
    return (row * COLUMNS + column) * 2


def lay_out(page: bytes, table: Table, left: Sequence[str], right: Sequence[str]) -> bytes:
    """`page` with its grid emptied, dakuten rows included, then filled row by row with `left` and `right`; the
    right block's edit row keeps dash, comma and space."""
    out = bytearray(page)
    attribute = page[_cell(LEFT_COLUMNS[0], GRID_ROWS[0]) + 1]
    for row in range(GRID_ROWS[0] - 1, GRID_ROWS[-1] + 1):
        for column in (*LEFT_COLUMNS, *RIGHT_COLUMNS):
            out[_cell(column, row) : _cell(column, row) + 2] = bytes([0, 0])
    for block, columns in ((left, LEFT_COLUMNS), (right, RIGHT_COLUMNS)):
        for row, letters in zip(GRID_ROWS, block, strict=False):
            for column, letter in zip(columns, letters, strict=False):
                out[_cell(column, row) : _cell(column, row) + 2] = bytes([table.to_bytes(letter)[0], attribute])
    edit = [*(table.to_bytes(key)[0] for key in EDIT_KEYS), SPACE_TILE]
    for column, code in zip(RIGHT_COLUMNS, edit, strict=False):
        out[_cell(column, EDIT_ROW) : _cell(column, EDIT_ROW) + 2] = bytes([code, attribute])
    return bytes(out)


def naming_grids_source(rom: bytes, table: Table) -> str:
    """The a816 module of the three French pages and the operands pointing the screen at them."""
    blocks = []
    patches = []
    for index, (address, operand, (left, right)) in enumerate(zip(PAGES, SOURCE_OPERANDS, LAYOUT, strict=True)):
        page = lay_out(decode(rom, rom_offset(address)), table, left, right)
        packed = encode(page)
        rows = [
            ", ".join(f"0x{code:02X}" for code in packed[start : start + 16]) for start in range(0, len(packed), 16)
        ]
        blocks += [f"naming_page{index}:", *(f"    .db {row}" for row in rows)]
        patches += [f".alloc at 0x{operand:06X} {{", f"    .dl naming_page{index}", "}"]
    return "\n".join(
        [
            '"""The naming screen\'s character pages for French names. Generated by build.py (utils/naming_screen.py)."""',
            "",
            '.include "src/expansion.i"',
            "",
            ".alloc naming_grids in expansion {",
            *blocks,
            "}",
            *patches,
            "",
        ]
    )


FONT_TILES = Path("src_assets/ee0020.bin")  # the 2bpp 8x8 menu font: the menus' digits, the screen's pages
SMALL_FONT = Path("assets/small_font.dat")
TILE_BYTES = 16
INK = 1
SHADOW = 3


def grid_codes(table: Table) -> set[int]:
    """Every code the pages type, the edit keys included."""
    letters = "".join("".join(rows) for page in LAYOUT for block in page for rows in block) + EDIT_KEYS
    return {table.to_bytes(letter)[0] for letter in letters}


REDRAWN = "".join(ACCENTS) + ".,'"  # still kana in the font; its letters, digits and other marks are already Latin


def redrawn_codes(table: Table) -> set[int]:
    """The codes the font draws as kana though the pages type them: only these are redrawn, so the menus, which
    share the font for their digits and letters, keep their glyphs."""
    return {table.to_bytes(letter)[0] for letter in REDRAWN}


def styled_tile(glyph: bytes, width: int) -> bytes:
    """A 1bpp 8x8 glyph as a 2bpp tile, centred in the cell: the letter in colour 1, its shadow one pixel right and
    down in colour 3, the way small_vwf draws the menus' names."""
    shift = max(0, (8 - width) // 2)
    ink = [row >> shift for row in glyph]
    pixels = [[0] * 8 for _ in range(8)]
    for y, row in enumerate(ink):
        for x in range(8):
            if row & (0x80 >> x):
                for dy, dx in ((1, 0), (0, 1), (1, 1)):
                    if y + dy < 8 and x + dx < 8 and not pixels[y + dy][x + dx]:
                        pixels[y + dy][x + dx] = SHADOW
    for y, row in enumerate(ink):
        for x in range(8):
            if row & (0x80 >> x):
                pixels[y][x] = INK
    tile = bytearray()
    for row in pixels:
        tile.append(sum(1 << (7 - x) for x in range(8) if row[x] & 1))
        tile.append(sum(1 << (7 - x) for x in range(8) if row[x] & 2))
    return bytes(tile)


def naming_font(tiles: bytes, font: VwfFont, codes: set[int]) -> bytes:
    """`tiles` with the glyph of each of `codes` redrawn from the 8x8 menu font."""
    out = bytearray(tiles)
    for code in codes:
        out[code * TILE_BYTES : (code + 1) * TILE_BYTES] = styled_tile(font.glyphs[code], font.widths[code])
    return bytes(out)


def naming_font_tiles(table: Table) -> bytes:
    return naming_font(FONT_TILES.read_bytes(), VwfFont.decode(SMALL_FONT.read_bytes()), redrawn_codes(table))
