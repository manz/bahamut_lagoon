import os
import struct
from unittest.case import TestCase

from script import Table

from utils.save_names import CHAPTER, CHECKSUM, EMPTY, NAME_SIZE, NAMES, SLOTS, checksum, name_record, rename

root_dir = os.path.join(os.path.dirname(__file__), "../..")


def save_with(chapters: list[int]) -> bytes:
    sram = bytearray(0x2000)
    for slot, chapter in zip(SLOTS, chapters, strict=True):
        sram[slot + CHAPTER] = chapter
        sram[slot + NAMES : slot + NAMES + 10 * NAME_SIZE] = bytes(range(1, 81))
    struct.pack_into("<H", sram, CHECKSUM, checksum(bytes(sram)))
    return bytes(sram)


class SaveNamesTestCase(TestCase):
    def setUp(self):
        self.table = Table(os.path.join(root_dir, "text/table/mz.tbl"))
        self.records = [
            name_record(self.table, name) for name in ["Byuu", "Yoyo"] + [f"Nom{index}" for index in range(8)]
        ]

    def test_a_name_is_padded_with_ff_to_eight_codes(self):
        self.assertEqual(name_record(self.table, "Byuu"), self.table.to_bytes("Byuu") + bytes([EMPTY] * 4))

    def test_a_long_name_is_cut_to_eight_codes(self):
        self.assertEqual(len(name_record(self.table, "Salamando")), NAME_SIZE)

    def test_a_used_slot_gets_the_names(self):
        patched = rename(save_with([EMPTY, 10, 11, 12]), self.records)
        start = SLOTS[1] + NAMES
        self.assertEqual(patched[start : start + NAME_SIZE], self.records[0])

    def test_an_empty_slot_is_left_alone(self):
        sram = save_with([EMPTY, 10, 11, 12])
        patched = rename(sram, self.records)
        start = SLOTS[0] + NAMES
        self.assertEqual(patched[start : start + 10 * NAME_SIZE], sram[start : start + 10 * NAME_SIZE])

    def test_the_checksum_matches_the_new_names(self):
        patched = rename(save_with([10, 11, 12, EMPTY]), self.records)
        self.assertEqual(struct.unpack_from("<H", patched, CHECKSUM)[0], checksum(patched))

    def test_nothing_past_the_names_changes(self):
        sram = save_with([10, 11, 12, EMPTY])
        patched = rename(sram, self.records)
        changed = {index for index in range(len(sram)) if sram[index] != patched[index]}
        names = {slot + NAMES + offset for slot in SLOTS[:3] for offset in range(10 * NAME_SIZE)}
        self.assertLessEqual(changed - names, {CHECKSUM, CHECKSUM + 1})
