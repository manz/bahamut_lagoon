from unittest import TestCase

from a816.exceptions import UnmappedBankError

from utils.cartridge import rom_address, rom_offset


class CartridgeTestCase(TestCase):
    def test_offset_of_rom_bank(self):
        self.assertEqual(rom_offset(0xC7140F), 0x07140F)

    def test_offset_of_expanded_bank(self):
        self.assertEqual(rom_offset(0xFFFFFF), 0x3FFFFF)

    def test_offset_of_low_mirror(self):
        self.assertEqual(rom_offset(0x408000), 0x008000)

    def test_offset_rejects_wram(self):
        with self.assertRaises(ValueError):
            rom_offset(0x7EBE00)

    def test_offset_rejects_unmapped_bank(self):
        with self.assertRaises(UnmappedBankError):
            rom_offset(0x806000)

    def test_address_lands_in_rom_banks(self):
        self.assertEqual(rom_address(0x07140F), 0xC7140F)

    def test_address_of_expanded_bank(self):
        self.assertEqual(rom_address(0x300000), 0xF00000)

    def test_address_rejects_offset_past_image(self):
        with self.assertRaises(ValueError):
            rom_address(0x400000)
