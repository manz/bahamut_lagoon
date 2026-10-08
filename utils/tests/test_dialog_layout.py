import os
import re
from unittest.case import TestCase

from utils.dialog_layout import LINE_WIDTH, NAME_CODES, NAME_LETTERS, RENAMEABLE, default_layout, script_overflows

root_dir = os.path.join(os.path.dirname(__file__), "../..")

LONG_LINE = "J'ai entendu dire que Commandant avait rejoint les Rebelles avant la bataille de Kana.[end]"


class DialogLayoutTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cwd = os.getcwd()
        os.chdir(root_dir)
        try:
            cls.layout = default_layout()
        finally:
            os.chdir(cwd)

    def test_a_fixed_name_measures_as_names_xml_spells_it(self):
        self.assertEqual(self.layout.width("[character][0xa]"), self.layout.width("Palparos"))

    def test_a_party_name_measures_as_eight_of_the_widest_letter(self):
        widest = max(self.layout.width(letter) for letter in NAME_LETTERS)
        self.assertEqual(self.layout.width("[character][0x0]"), widest * NAME_CODES)

    def test_every_party_name_takes_the_worst_case(self):
        widths = {self.layout.width(f"[character][{index:#x}]") for index in range(RENAMEABLE)}
        self.assertEqual(len(widths), 1)

    def test_terminators_take_no_width(self):
        self.assertEqual(self.layout.width("Salut ![end]"), self.layout.width("Salut !"))

    def test_an_empty_line_is_zero_pixels(self):
        self.assertEqual(self.layout.width(""), 0)

    def test_short_lines_of_a_paragraph_are_joined(self):
        self.assertEqual(self.layout.reflow("Allez !\nDépêchons-nous ![end]"), "Allez ! Dépêchons-nous ![end]")

    def test_a_line_wider_than_the_window_breaks_at_spaces(self):
        self.assertEqual(self.layout.reflow(LONG_LINE).replace("\n", " "), LONG_LINE)

    def test_every_reflowed_line_fits_the_window(self):
        widths = [self.layout.width(line) for line in self.layout.reflow(LONG_LINE).split("\n")]
        self.assertLessEqual(max(widths), LINE_WIDTH)

    def test_a_long_sentence_takes_as_few_lines_as_filling_would(self):
        lines = self.layout.reflow(LONG_LINE).split("\n")
        self.assertEqual(len(lines), 2)

    def test_a_long_sentence_is_balanced_over_its_lines(self):
        widths = [self.layout.width(line) for line in self.layout.reflow(LONG_LINE).split("\n")]
        self.assertLess(max(widths) - min(widths), LINE_WIDTH // 3)

    def test_short_sentences_share_a_line(self):
        self.assertEqual(
            self.layout.reflow("C'est inutile !\nIl n'y a personne ![end]"), "C'est inutile ! Il n'y a personne ![end]"
        )

    def test_a_sentence_that_does_not_fit_after_the_line_starts_its_own(self):
        text = "Capitaine Truth ! Voulez-vous attaquer sans être certain de savoir ce que vous allez faire ?[end]"
        self.assertTrue(self.layout.reflow(text).startswith("Capitaine Truth !\n"))

    def test_the_tail_of_a_wrapped_sentence_takes_no_other_sentence(self):
        text = "Voulez-vous attaquer sans être certain de savoir ce que vous allez faire ? Et ensuite ?[end]"
        self.assertTrue(self.layout.reflow(text).endswith("\nEt ensuite ?[end]"))

    def test_a_question_mark_stays_with_its_word(self):
        text = "Bikkebakke: Veux-tu connaître les noms les plus populaires de tout le royaume ?[end]"
        self.assertFalse(any(line.startswith("?") for line in self.layout.reflow(text).split("\n")))

    def test_blank_lines_separate_paragraphs(self):
        self.assertEqual(self.layout.reflow("Un.\n\nDeux.[end]"), "Un.\n\nDeux.[end]")

    def test_lines_starting_with_a_space_are_kept(self):
        card = "                    Prologue\n                La Chute de Kana[end]"
        self.assertEqual(self.layout.reflow(card), card)

    def test_a_speaker_label_keeps_its_own_line(self):
        self.assertEqual(
            self.layout.reflow("[character][0x1]:\nMerci.\nAdieu.[end]"), "[character][0x1]:\nMerci. Adieu.[end]"
        )

    def test_a_heading_keeps_its_own_line(self):
        self.assertEqual(self.layout.reflow("-Aller-\nTon dragon attaque.[end]"), "-Aller-\nTon dragon attaque.[end]")

    def test_a_text_before_a_choice_is_kept(self):
        self.assertEqual(self.layout.reflow("Oui\nNon[end1]"), "Oui\nNon[end1]")

    def test_the_reflowed_french_script_fits_the_window(self):
        cwd = os.getcwd()
        os.chdir(root_dir)
        try:
            overflows = list(script_overflows(self.layout))
        finally:
            os.chdir(cwd)
        self.assertEqual(overflows, [])

    def test_reflowing_twice_changes_nothing(self):
        once = self.layout.reflow(LONG_LINE)
        self.assertEqual(self.layout.reflow(once), once)

    def test_reflow_keeps_every_word(self):
        text = "Capitaine [character][0x0] !\nVoulez-vous attaquer sans\nsavoir ?[end]"
        self.assertEqual(re.split(r"\s+", self.layout.reflow(text)), re.split(r"\s+", text))
