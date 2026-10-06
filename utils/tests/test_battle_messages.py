from unittest import TestCase

from script import Table

from utils.battle_messages import BANK_SITES, LINE, LINE_BUS, BattleMessage, patches, read_messages

TABLE = Table("text/table/mz.tbl")
ADDRESS = 0xFD8000


class PatchesTestCase(TestCase):
    def test_loaders_read_the_new_bank(self):
        _, code = patches(TABLE, [], ADDRESS)
        self.assertEqual({site: code[site] for site in BANK_SITES}, {site: b"\xfd" for site in BANK_SITES})

    def test_references_point_at_the_relocated_strings(self):
        messages = [BattleMessage("Oui", (0xC01000,)), BattleMessage("Non", (0xC02000, 0xC03000))]
        _, code = patches(TABLE, messages, ADDRESS)
        self.assertEqual([code[0xC01001], code[0xC02001], code[0xC03001]], [b"\x00\x80", b"\x04\x80", b"\x04\x80"])

    def test_a_prefix_copies_its_text_alone(self):
        _, code = patches(TABLE, [BattleMessage("Chapitre ", (0xC01000,), 0xC01005, "prefix")], ADDRESS)
        self.assertEqual(code[0xC01006], bytes([9]))

    def test_a_line_copies_its_ff_too(self):
        _, code = patches(TABLE, [BattleMessage("Oui", (0xC01000,), 0xC01005)], ADDRESS)
        self.assertEqual(code[0xC01006], bytes([4]))

    def test_a_shared_count_takes_the_longest(self):
        messages = [BattleMessage("Oui", (0xC01000,), 0xC01005), BattleMessage("Plus long", (0xC02000,), 0xC01005)]
        _, code = patches(TABLE, messages, ADDRESS)
        self.assertEqual(code[0xC01006], bytes([10]))

    def test_digits_follow_the_text(self):
        _, code = patches(TABLE, [BattleMessage("Exp. : ", (0xC01000,), digits=0xC01010)], ADDRESS)
        self.assertEqual(code[0xC01011], (LINE + 7).to_bytes(2, "little"))

    def test_a_digit_goes_where_its_mark_is(self):
        _, code = patches(TABLE, [BattleMessage("Reste (#)", (0xC01000,), digit=0xC01010)], ADDRESS)
        self.assertEqual(code[0xC01011], (LINE_BUS + 7).to_bytes(2, "little"))


class MessagesTestCase(TestCase):
    def test_every_message_fits_the_battle_line(self):
        for message in read_messages():
            with self.subTest(text=message.text):
                self.assertLessEqual(len(message.text), 0x20)

    def test_every_message_encodes(self):
        for message in read_messages():
            with self.subTest(text=message.text):
                text = message.text.replace("#", "0")
                codes = TABLE.to_bytes(text.replace(" ", r"\s"))
                self.assertEqual(TABLE.to_text(codes).replace(r"\s", " "), text)
