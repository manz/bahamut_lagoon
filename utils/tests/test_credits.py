from unittest import TestCase

from utils.credits import COLUMNS, STEP, credits_script


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
