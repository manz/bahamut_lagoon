from unittest import TestCase

from script import Table

from utils.items import ITEM_COUNT, NAME_SIZE, item_name_records

TABLE = Table("text/table/battle_jp.tbl")


def items_xml(*names: tuple[str, str]) -> str:
    strings = "".join(f'<string icon="{icon}">{name}</string>' for icon, name in names)
    return f"<item_names>{strings}</item_names>"


def full_table(first: tuple[str, str]) -> str:
    return items_xml(first, *[("0xe0", "ア")] * (ITEM_COUNT - 1))


class ItemNameRecordsTestCase(TestCase):
    def test_short_name_ends_with_ff_then_padding(self):
        record = item_name_records(full_table(("0xd5", "アア")), TABLE)[:9]
        self.assertEqual(record, bytes([0xD5, 0x7F, 0x7F, 0xFF]) + bytes([0xFE] * 5))

    def test_full_name_has_no_terminator(self):
        record = item_name_records(full_table(("0xd5", "ア" * NAME_SIZE)), TABLE)[:9]
        self.assertEqual(record, bytes([0xD5]) + bytes([0x7F] * NAME_SIZE))

    def test_rejects_name_longer_than_the_record(self):
        with self.assertRaises(ValueError):
            item_name_records(full_table(("0xd5", "ア" * (NAME_SIZE + 1))), TABLE)

    def test_rejects_wrong_item_count(self):
        with self.assertRaises(ValueError):
            item_name_records(items_xml(("0xd5", "ア")), TABLE)

    def test_rejects_missing_icon(self):
        xml = full_table(("0xd5", "ア")).replace('icon="0xd5"', "", 1)
        with self.assertRaises(ValueError):
            item_name_records(xml, TABLE)
