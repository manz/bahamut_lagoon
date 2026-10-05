from unittest import TestCase

from utils.ips import apply_ips


def record(offset: int, data: bytes) -> bytes:
    return offset.to_bytes(3, "big") + len(data).to_bytes(2, "big") + data


class ApplyIpsTestCase(TestCase):
    def test_record_overwrites_bytes(self):
        patch = b"PATCH" + record(1, b"\xaa\xbb") + b"EOF"
        self.assertEqual(apply_ips(b"\x00\x00\x00\x00", patch), b"\x00\xaa\xbb\x00")

    def test_rle_record_repeats_byte(self):
        patch = b"PATCH" + (2).to_bytes(3, "big") + b"\x00\x00" + (3).to_bytes(2, "big") + b"\xee" + b"EOF"
        self.assertEqual(apply_ips(bytes(6), patch), b"\x00\x00\xee\xee\xee\x00")

    def test_record_past_end_grows_rom(self):
        patch = b"PATCH" + record(4, b"\x11") + b"EOF"
        self.assertEqual(apply_ips(b"\x00\x00", patch), b"\x00\x00\x00\x00\x11")

    def test_rejects_non_ips(self):
        with self.assertRaises(ValueError):
            apply_ips(b"", b"NOPE")
