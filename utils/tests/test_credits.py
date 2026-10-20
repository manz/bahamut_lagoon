import xml.etree.ElementTree as ET
from unittest import TestCase

from script import Table

from utils.credits import COLUMNS, SCREEN_COLUMNS, STEP, TABLE, credits_script, place_credit_lines
from utils.vm.opcodes_map import opcode_names, opcode_table
from utils.vm.room import Room


class CreditsScriptTestCase(TestCase):
    def test_a_line_is_centred_and_stepped(self) -> None:
        margin = (STEP + " ") * ((COLUMNS - 4) // 2)
        self.assertEqual(credits_script("TEAM[end1]"), f"{margin}{STEP}T{STEP}E{STEP}A{STEP}M{STEP}[end1]")

    def test_the_odd_column_goes_to_the_left_margin(self) -> None:
        self.assertEqual(credits_script("abc[end1]").count(" "), (COLUMNS - 3 + 1) // 2)

    def test_every_line_is_spelled(self) -> None:
        first, second = credits_script("a\nb[end1]").split("\n")
        self.assertEqual((first.endswith(f"{STEP}a{STEP}"), second.endswith(f"{STEP}b{STEP}[end1]")), (True, True))

    def test_the_last_credit_ends_without_a_step(self) -> None:
        self.assertTrue(credits_script("ab[end][end]").endswith(f"{STEP}b[end][end]"))

    def test_a_code_without_a_letter_is_one_column(self) -> None:
        self.assertEqual(credits_script("[0x37][end1]").count(" "), (COLUMNS - 1 + 1) // 2)

    def test_a_line_wider_than_the_columns_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            credits_script("a" * (COLUMNS + 1) + "[end1]")


class PlaceCreditLinesTestCase(TestCase):
    """draw_credit_line(x, y, text) at 0, its text at 6: the x operand is the ref's address less two."""

    SCRIPT = bytes([0x85, 0x10, 0x07, 0x06, 0x00, 0xFF, 0x01, 0xFF])

    def room(self) -> Room:
        return Room(bytearray(self.SCRIPT), opcode_table, opcode_names, Table(str(TABLE)))

    @staticmethod
    def texts(line: str, x: int | None = None) -> ET.Element:
        column = "" if x is None else f' x="{x}"'
        return ET.fromstring(f"<texts><text{column}><refs><ref>0x3</ref></refs><data>{line}</data></text></texts>")

    def test_a_line_with_a_column_moves_there(self) -> None:
        room = self.room()
        place_credit_lines(room, self.texts("et[end]", 21))
        self.assertEqual(room.room[1], 21)

    def test_a_line_without_a_column_stays(self) -> None:
        room = self.room()
        place_credit_lines(room, self.texts("et[end]"))
        self.assertEqual(room.room[1], 0x10)

    def test_a_moved_line_past_the_right_edge_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            place_credit_lines(self.room(), self.texts("abc[end]", SCREEN_COLUMNS - 2))

    def test_a_line_that_grew_past_the_right_edge_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            place_credit_lines(self.room(), self.texts("a" * (SCREEN_COLUMNS - 0x10 + 1) + "[end]"))
