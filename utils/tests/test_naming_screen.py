import os
from pathlib import Path
from unittest.case import TestCase

from katsuji.formats import VwfFont
from script import Table

from utils.cartridge import rom_offset
from utils.naming_screen import (
    COLUMNS,
    GRID_ROWS,
    LAYOUT,
    LEFT_COLUMNS,
    PAGES,
    RIGHT_COLUMNS,
    decode,
    encode,
    grid_codes,
    lay_out,
    naming_font,
    redrawn_codes,
    styled_tile,
)

root_dir = os.path.join(os.path.dirname(__file__), "../..")
DAKUTEN = (0x31, 0x32)


class NamingScreenTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(root_dir, "build/bl.sfc"), "rb") as rom:
            cls.rom = rom.read()
        cls.table = Table(os.path.join(root_dir, "text/table/mz.tbl"))
        cls.pages = [decode(cls.rom, rom_offset(address)) for address in PAGES]

    def test_the_vanilla_pages_unpack_to_full_maps(self):
        self.assertEqual({len(page) for page in self.pages}, {0x800})

    def test_packing_round_trips(self):
        for page in self.pages:
            self.assertEqual(decode(encode(page), 0), page)

    def test_an_escape_byte_round_trips(self):
        data = bytes([0x1A, 0x1B, 0x00, 0x1A] * 8)
        self.assertEqual(decode(encode(data), 0), data)

    def test_packing_is_no_bigger_than_the_vanilla_pages(self):
        vanilla = [len(encode(page)) for page in self.pages]
        self.assertLessEqual(vanilla[0], 336)

    def _cells(self, page, rows, columns):
        return [page[(row * COLUMNS + column) * 2] for row in rows for column in columns]

    def test_no_dakuten_mark_is_left_in_a_grid(self):
        for page, (left, right) in zip(self.pages, LAYOUT, strict=True):
            laid = lay_out(page, self.table, left, right)
            rows = range(GRID_ROWS[0] - 1, GRID_ROWS[-1] + 1)
            self.assertFalse(set(self._cells(laid, rows, (*LEFT_COLUMNS, *RIGHT_COLUMNS))) & set(DAKUTEN))

    def test_the_capitals_page_starts_with_a(self):
        laid = lay_out(self.pages[0], self.table, *LAYOUT[0])
        self.assertEqual(self._cells(laid, [GRID_ROWS[0]], LEFT_COLUMNS[:1]), [self.table.to_bytes("A")[0]])

    def test_every_typed_code_has_a_glyph_in_both_fonts(self):
        small = VwfFont.decode(Path(root_dir, "assets/small_font.dat").read_bytes())
        dialog = VwfFont.decode(Path(root_dir, "assets/vwf.bin").read_bytes())
        for code in grid_codes(self.table):
            self.assertTrue(any(small.glyphs[code]), hex(code))
            self.assertTrue(any(dialog.glyphs[code]), hex(code))

    def test_a_styled_tile_puts_ink_in_colour_1_and_its_shadow_in_colour_3(self):
        tile = styled_tile(bytes([0x80] + [0] * 7), 1)
        planes = [(tile[2 * row], tile[2 * row + 1]) for row in range(8)]
        ink = planes[0][0] & 0x10 and not planes[0][1] & 0x10  # centred in the cell: column 3
        shadow = planes[1][0] & 0x08 and planes[1][1] & 0x08  # one down and right
        self.assertTrue(ink and shadow)

    def test_only_the_grid_codes_change_in_the_font(self):
        small = VwfFont.decode(Path(root_dir, "assets/small_font.dat").read_bytes())
        tiles = Path(root_dir, "src_assets/ee0020.bin").read_bytes()
        codes = redrawn_codes(self.table)
        font = naming_font(tiles, small, codes)
        changed = {index // 16 for index in range(len(tiles)) if tiles[index] != font[index]}
        self.assertLessEqual(changed, codes)

    def test_the_digits_and_letters_the_menus_use_are_not_redrawn(self):
        codes = redrawn_codes(self.table)
        for text in ("0123456789", "ABCZ", "abcz"):
            self.assertFalse(set(self.table.to_bytes(text)) & codes, text)
