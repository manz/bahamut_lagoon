import os
import re
from unittest.case import TestCase

from utils.dialog_layout import (
    LINE_WIDTH,
    NAME_CODES,
    NAME_LETTERS,
    RENAMEABLE,
    default_layout,
    script_overflows,
    typeset,
)

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

    def test_a_line_starting_with_one_space_is_kept(self):
        choice = " Oui\n Non"
        self.assertEqual(self.layout.reflow(choice + "[end]"), choice + "[end]")

    def test_a_line_starting_with_two_spaces_is_centred(self):
        line = self.layout.reflow("  Prologue[end]")
        left = self.layout.width(line[: len(line) - len(line.lstrip(" "))])
        right = LINE_WIDTH - left - self.layout.width("Prologue")
        self.assertLessEqual(abs(left - right), self.layout.width(" "))

    def test_a_centred_name_sits_at_its_default_width(self):
        def indent(line: str) -> int:
            return len(line) - len(line.lstrip(" "))

        self.assertEqual(indent(self.layout.centre("  -[character][0x0]-")), indent(self.layout.centre("  -Byuu-")))

    def test_a_block_that_would_cross_the_window_starts_the_next(self):
        text = "Un.\nVoulez-vous attaquer sans être certain de savoir ce que vous allez faire demain matin ?[end]"
        lines = self.layout.reflow(text, page_lines=2).split("\n")
        self.assertEqual(lines[:2], ["Un.", ""])

    def test_a_speaker_label_stays_with_its_text_across_windows(self):
        text = "Un.\n\nYoyo:\nVoulez-vous attaquer sans être certain de savoir ce que vous allez faire ?[end]"
        lines = self.layout.reflow(text, page_lines=3).split("\n")
        self.assertEqual(lines[3], "Yoyo:")

    def test_a_line_of_spaces_is_a_blank_line(self):
        self.assertEqual(self.layout.reflow("Un.\n  \nDeux.[end]"), "Un.\n\nDeux.[end]")

    def test_a_line_of_spaces_does_not_open_a_window(self):
        lines = self.layout.reflow("Un. Deux. Trois.\n \nQuatre.[end]", page_lines=1).split("\n")
        self.assertNotIn("", lines)

    def test_a_line_set_right_of_centre_is_right_aligned(self):
        lines = self.layout.reflow("Personne ne doit entrer !\n                      -Matelight-[end]").split("\n")
        self.assertGreater(self.layout.width(lines[1]), LINE_WIDTH - self.layout.width(" ") - 1)

    def test_lines_sharing_one_indent_are_kept(self):
        letter = "    Comment te portes-tu ?\n    Où es-tu ?[end]"
        self.assertEqual(self.layout.reflow(letter), letter)

    def test_numbered_lines_stay_one_a_line(self):
        ranking = "[0xb0]- SALAMANDO\n[0xb1]- POCHI\n[0xb2]- TANAKA[end]"
        self.assertEqual(self.layout.reflow(ranking), ranking)

    def test_a_choice_prompt_keeps_its_lines(self):
        prompt = "Que fais-tu ?\nAttaquer\nFuir[end]"
        self.assertEqual(self.layout.reflow(prompt, keep_lines=True), prompt)

    def test_a_blank_line_does_not_open_a_window(self):
        lines = self.layout.reflow("Un.\nDeux ?\n\nTrois.[end]", page_lines=1).split("\n")
        self.assertNotIn("", lines)

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


class TypesetTestCase(TestCase):
    def test_a_comma_is_followed_by_a_space(self):
        self.assertEqual(typeset("Pour une fois,écoute-moi"), "Pour une fois, écoute-moi")

    def test_a_decimal_comma_is_left_alone(self):
        self.assertEqual(typeset("1,5 lagon"), "1,5 lagon")

    def test_a_comma_before_a_name_gets_its_space(self):
        self.assertEqual(typeset("Merci,[character][0x0]."), "Merci, [character][0x0].")

    def test_an_ellipsis_running_into_a_word_gets_a_space(self):
        self.assertEqual(typeset("Je...je"), "Je... je")

    def test_an_ellipsis_before_punctuation_stays_tight(self):
        self.assertEqual(typeset("Quoi...?"), "Quoi... ?")

    def test_question_and_exclamation_marks_get_their_space(self):
        self.assertEqual(typeset("Viens!"), "Viens !")

    def test_runs_of_spaces_collapse_but_not_the_indentation(self):
        self.assertEqual(typeset("    Un  deux"), "    Un deux")

    def test_an_ellipsis_before_the_terminator_stays_tight(self):
        self.assertEqual(typeset("Vint alors la nuit...[end]"), "Vint alors la nuit...[end]")

    def test_a_name_gets_a_space_before_an_exclamation_mark(self):
        self.assertEqual(typeset("le seigneur [character][0x0]!"), "le seigneur [character][0x0] !")

    def test_a_glyph_code_keeps_what_follows_tight(self):
        self.assertEqual(typeset("Princesse[0xd8]!"), "Princesse[0xd8]!")

    def test_a_colon_in_a_sentence_gets_its_space(self):
        self.assertEqual(typeset("Nous vous l'annonçons en ces lieux:"), "Nous vous l'annonçons en ces lieux :")

    def test_a_speaker_colon_stays_as_the_script_writes_it(self):
        self.assertEqual(typeset("Roi de Kana: Bonjour."), "Roi de Kana: Bonjour.")

    def test_a_named_speaker_colon_stays_too(self):
        self.assertEqual(typeset("[character][0x1]: Merci."), "[character][0x1]: Merci.")

    def test_typesetting_twice_changes_nothing(self):
        once = typeset("Pour une fois,écoute...moi!")
        self.assertEqual(typeset(once), once)
