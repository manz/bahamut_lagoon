from unittest import TestCase

from utils.small_vwf_bake import MAX_CELLS, TILE, bake, render

BAR = bytes([0x80] * 8 + [1])  # code 1: a one-pixel column, one pixel wide
WIDE = bytes([0xFF] * 8 + [8])  # every other code: a full cell
FONT = b"".join(BAR if code == 1 else WIDE for code in range(256))


class RenderTestCase(TestCase):
    def test_the_shadow_falls_right_in_colour_3(self):
        tiles, cells = render(FONT, b"\x01")
        self.assertEqual(cells, 1)
        self.assertEqual(tiles[0:2], bytes([0xC0, 0x40]))  # ink at column 0 (colour 1), shadow at 1 (colour 3)

    def test_the_ink_above_shades_nothing_under_ink(self):
        tiles, _ = render(FONT, b"\x01")
        self.assertEqual(tiles[2:4], bytes([0xC0, 0x40]))

    def test_the_pen_advances_by_the_width_and_the_shadow_gap(self):
        tiles, _ = render(FONT, b"\x01\x01")
        self.assertEqual(tiles[0], 0xF0)  # ink at 0 and 2, shadows at 1 and 3

    def test_cells_cover_the_pen(self):
        self.assertEqual(render(FONT, b"\x02")[1], 2)  # 8 pixels and the gap: the pen is in cell 1

    def test_glyphs_past_max_cells_are_dropped(self):
        tiles, cells = render(FONT, b"\x02" * 4, max_cells=2)
        self.assertEqual(cells, 2)
        self.assertEqual(tiles[2 * TILE :], bytes((MAX_CELLS - 2) * TILE))

    def test_tiles_past_the_cells_are_clear(self):
        tiles, cells = render(FONT, b"\x01")
        self.assertEqual(tiles[cells * TILE :], bytes((MAX_CELLS - cells) * TILE))

    def test_an_end_code_stops_the_string(self):
        self.assertEqual(render(FONT, b"\x01\xff\x02"), render(FONT, b"\x01"))

    def test_a_long_string_stops_at_the_cells(self):
        self.assertEqual(render(FONT, b"\x02" * 30)[1], MAX_CELLS)


class BakeTestCase(TestCase):
    def test_entries_point_at_each_names_tiles(self):
        blob = bytearray()
        entries = bake(FONT, [b"\x01", b"\x02"], blob, {})
        self.assertEqual([(entry.offset, entry.cells) for entry in entries], [(0, 1), (TILE, 2)])
        self.assertEqual(blob[TILE:], render(FONT, b"\x02")[0][: 2 * TILE])

    def test_identical_tiles_are_stored_once(self):
        blob = bytearray()
        entries = bake(FONT, [b"\x02", b"\x02"], blob, {})
        self.assertEqual(entries[0], entries[1])
        self.assertEqual(len(blob), 2 * TILE)

    def test_more_than_a_bank_fails(self):
        font = b"".join(bytes([code] * 8 + [8]) for code in range(256))  # every code its own full-width rows
        names = [bytes([code, other] + [code] * 9) for code in range(1, 256) for other in range(1, 4)]
        with self.assertRaises(ValueError):
            bake(font, names, bytearray(), {})
