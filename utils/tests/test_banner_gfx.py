import hashlib
from pathlib import Path
from unittest import TestCase

from utils.banner_gfx import (
    Banner,
    compress_interleaved,
    decompress,
    decompress_interleaved,
    pack_flips,
    read_banner,
    unpack_flips,
)
from utils.decompress_gfx import compress_asset

root_dir = Path(__file__).parents[2]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


class AssetLzTestCase(TestCase):
    def test_an_escaped_control_byte_is_a_literal(self) -> None:
        self.assertEqual(decompress(b"\x01\x1a\x00\x00\x1b\x00\x01")[0], b"\x1a")

    def test_a_back_reference_repeats_what_was_written(self) -> None:
        self.assertEqual(decompress(b"\x01ab\x1a\x04\x02\x1a\x00\x01")[0], b"ababab")

    def test_its_end_is_past_the_end_word(self) -> None:
        self.assertEqual(decompress(b"\x01a\x1a\x00\x01xx")[1], 5)

    def test_compressed_data_decompresses_to_itself(self) -> None:
        data = bytes(range(64)) * 8 + b"\x1a\x1b" * 4
        self.assertEqual(decompress(compress_asset(data))[0], data)


class InterleavedLzTestCase(TestCase):
    def test_a_1a_end_word_is_a_back_reference(self) -> None:
        with self.assertRaises(IndexError):
            decompress_interleaved(b"\x01\x1a\x00\x01")

    def test_compressed_data_decompresses_to_itself(self) -> None:
        data = bytes(range(16)) * 32
        self.assertEqual(decompress_interleaved(compress_interleaved(data))[0], data)


class FlipsTestCase(TestCase):
    def test_fields_are_read_low_bits_first(self) -> None:
        self.assertEqual(unpack_flips(b"\x04\x01\x00\xe4"), b"\x00\x01\x02\x03")

    def test_packed_flips_unpack_to_themselves(self) -> None:
        flips = bytes([0, 1, 2, 3, 3, 2, 1, 0])
        self.assertEqual(unpack_flips(pack_flips(flips)), flips)


class BannerTestCase(TestCase):
    """The digests are of what the game leaves in VRAM (0x3000 tiles, 0x5000 map) under the PLAYER PHASE banner."""

    banner: Banner

    @classmethod
    def setUpClass(cls) -> None:
        cls.banner = read_banner((root_dir / "build/bl.sfc").read_bytes())

    def test_the_tiles_are_the_games(self) -> None:
        self.assertEqual(digest(self.banner.tiles), "0955727a6a5dc8cb")

    def test_the_tilemap_is_the_games(self) -> None:
        self.assertEqual(digest(self.banner.tilemap()), "547dfaf22fe266ea")

    def test_its_streams_read_back_as_the_banner(self) -> None:
        tiles, tile_numbers, flips = self.banner.streams()
        read = Banner(decompress(tiles)[0], decompress_interleaved(tile_numbers)[0], unpack_flips(decompress(flips)[0]))
        self.assertEqual(read, self.banner)
