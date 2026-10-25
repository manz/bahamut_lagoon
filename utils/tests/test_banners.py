from pathlib import Path
from unittest import TestCase

import numpy as np

from utils.banner_gfx import read_banner
from utils.banners import (
    ENGLISH,
    MAX_TILES,
    compose,
    french_banner,
    pixels_of,
    read_font,
    read_small_font,
    tiles_of,
)

root_dir = Path(__file__).parents[2]


class ComposeTestCase(TestCase):
    def test_the_english_texts_draw_the_games_banners(self) -> None:
        game = pixels_of(read_banner((root_dir / "build/bl.sfc").read_bytes()))
        drawn = compose(ENGLISH, read_font(root_dir / "src_assets/banner_font.png"), read_small_font())
        self.assertTrue(np.array_equal(drawn, game))


class TilesOfTestCase(TestCase):
    def test_its_tiles_draw_the_image(self) -> None:
        image = compose(ENGLISH, read_font(root_dir / "src_assets/banner_font.png"), read_small_font())
        self.assertTrue(np.array_equal(pixels_of(tiles_of(image)), image))

    def test_a_flipped_tile_is_drawn_from_the_same_tile(self) -> None:
        image = np.zeros((128 * 8, 32 * 8), np.uint8)
        image[0, 0] = 1
        image[7, 7] = 2
        image[8, 7] = 1
        image[15, 0] = 2
        banner = tiles_of(image)
        self.assertEqual((banner.tile_numbers[32], banner.flips[32]), (0, 1))

    def test_more_tiles_than_the_game_uploads_are_refused(self) -> None:
        image = np.zeros((128 * 8, 32 * 8), np.uint8)
        for tile in range(MAX_TILES + 1):
            top, left = tile // 32 * 8, tile % 32 * 8
            image[top, left] = 1  # no tile is another's flip
            image[top + 3, left : left + 8] = np.unpackbits(np.uint8(tile)) * 2
            image[top + 4, left : left + 8] = np.unpackbits(np.uint8(tile >> 8)) * 2
        with self.assertRaises(ValueError):
            tiles_of(image)


class FrenchBannerTestCase(TestCase):
    def test_it_fits_the_tiles_the_game_uploads(self) -> None:
        self.assertLessEqual(len(french_banner().tiles) // 32, MAX_TILES)
