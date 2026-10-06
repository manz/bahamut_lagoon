from unittest import TestCase

from script import Table

from utils.name_tables import NAME_TABLES, item_records, long_names_source, read_names, short_record

TABLE = Table("text/table/mz.tbl")


class ShortRecordTestCase(TestCase):
    def test_short_name_ends_with_ff(self):
        self.assertEqual(short_record(b"\x01\x02"), b"\x01\x02\xff\xfe\xfe\xfe\xfe\xfe")

    def test_eight_codes_fill_the_record(self):
        self.assertEqual(short_record(bytes(range(8))), bytes(range(8)))

    def test_long_name_is_cut_to_the_record(self):
        self.assertEqual(short_record(bytes(range(12))), bytes(range(8)))


class NameTablesTestCase(TestCase):
    def test_every_name_encodes(self):
        for name_table in NAME_TABLES:
            for name in read_names(name_table.source):
                with self.subTest(table=name_table.label, name=name):
                    codes = TABLE.to_bytes(name.replace(" ", r"\s"))
                    self.assertEqual(TABLE.to_text(codes).replace(r"\s", " "), name)

    def test_names_drop_the_ff_suffix(self):
        self.assertEqual(read_names(NAME_TABLES[0].source)[0], "Byuu")


class LongNamesSourceTestCase(TestCase):
    def test_descriptors_end_with_a_null_record(self):
        source = long_names_source(TABLE)
        self.assertIn("    .dl 0x000000", source)

    def test_one_descriptor_per_table(self):
        source = long_names_source(TABLE)
        for name_table in NAME_TABLES:
            with self.subTest(table=name_table.label):
                self.assertIn(f"    .dl 0x{name_table.address:06X}", source)

    def test_strings_end_with_ff(self):
        source = long_names_source(TABLE)
        self.assertIn("_class_names_0:\n    .db 0x", source)
        line = source.split("_class_names_0:\n")[1].splitlines()[0]
        self.assertTrue(line.endswith(", 0xFF"))


class ItemRecordsTestCase(TestCase):
    def test_a_record_is_the_icon_then_the_cut_name(self):
        records = item_records(TABLE)
        self.assertEqual(len(records), 128 * 9)
        self.assertEqual(records[9], 0xD5)  # Epée longue, a sword

    def test_short_name_ends_with_ff_after_the_icon(self):
        self.assertEqual(item_records(TABLE)[0:7], bytes([0xEF, *TABLE.to_bytes("Aucun"), 0xFF]))
