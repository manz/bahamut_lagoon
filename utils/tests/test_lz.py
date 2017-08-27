from unittest.case import TestCase

from utils.lz import find_pattern, lz_compress, lz_decompress


class LZCompressionTestCase(TestCase):
    def test_find_pattern_repeat_single(self):
        pattern = find_pattern(b'\x00', b'\x00' * 18)

        self.assertIsNotNone(pattern)
        self.assertEqual(pattern[0], 1)
        self.assertEqual(pattern[1], 18)

    def test_find_pattern_repeat_sequence(self):
        pattern_to_find = b'\x00\x01\x03\x04'
        data = b'\x00\x01\x03\x04\x00\x01\x03\x04\x00' \
               b'\x01\x03\x04\x00\x01\x03\x04\x00\x01'

        pattern = find_pattern(pattern_to_find, data)
        self.assertEquals(pattern[0], 4)
        self.assertEquals(pattern[1], 18)

    def test_find_pattern_repeat_last(self):
        pattern_to_find = bytearray(b'r\x05\x08\x8b\x8d\x00')
        data = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

        pattern = find_pattern(pattern_to_find, data)
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern[0], 1)
        self.assertEqual(pattern[1], 18)

    def test_compress(self):
        data = b'\x00\x01\x03\x04\x00\x01\x03\x04\x00' \
               b'\x01\x03\x04\x00\x01\x03\x04\x00\x01'

        compressed = lz_compress(data)
        decompressed = lz_decompress(compressed)
        # for now we pad with \xff (we loose at most 6 bytes where we need 3
        # bytes for continuation and at most 6 bytes of data ...
        self.assertEqual(decompressed, data + b'\xff\xff')
