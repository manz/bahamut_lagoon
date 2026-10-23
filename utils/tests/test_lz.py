from unittest.case import TestCase

from utils.lz import find_pattern, lz_compress, lz_decompress


class LZCompressionTestCase(TestCase):
    def test_find_pattern_repeat_single(self) -> None:
        self.assertEqual(find_pattern(b"\x00", b"\x00" * 18), (1, 18))

    def test_find_pattern_repeat_sequence(self) -> None:
        pattern_to_find = b"\x00\x01\x03\x04"
        data = b"\x00\x01\x03\x04\x00\x01\x03\x04\x00\x01\x03\x04\x00\x01\x03\x04\x00\x01"

        self.assertEqual(find_pattern(pattern_to_find, data), (4, 18))

    def test_find_pattern_repeat_last(self) -> None:
        pattern_to_find = bytearray(b"r\x05\x08\x8b\x8d\x00")
        data = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")

        self.assertEqual(find_pattern(pattern_to_find, data), (1, 18))

    def test_compress(self) -> None:
        data = b"\x00\x01\x03\x04\x00\x01\x03\x04\x00\x01\x03\x04\x00\x01\x03\x04\x00\x01"

        # the last flag group is filled with FF literals, which decompress to the end of the block reads back
        self.assertEqual(lz_decompress(lz_compress(data)), data + b"\xff\xff\xff")

    def test_a_block_reaches_into_the_ones_before(self) -> None:
        previous = bytearray(b"abcd")
        self.assertEqual(lz_decompress(b"\x01\x04\x00", previous), b"abcdabc")
