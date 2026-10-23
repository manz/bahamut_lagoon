from unittest import TestCase, skipUnless

from utils.battle_walk import IPS, ROM, ROOMS, fr_rom, room_script
from utils.vm.battle_asm import assemble, encode, encode_script, op
from utils.vm.battle_script import disassemble, instruction


@skipUnless(ROM.exists(), "needs build/bl.sfc")
class ReencodeTestCase(TestCase):
    def test_every_vanilla_room_reencodes_to_its_script(self) -> None:
        self.assertEqual([r for r in range(ROOMS) if encode_script(disassemble(d := room_script(r))) != d], [])

    @skipUnless(IPS.exists(), "needs build/bl.ips")
    def test_every_french_room_reencodes_to_its_script(self) -> None:
        rom = fr_rom()
        self.assertEqual([r for r in range(ROOMS) if encode_script(disassemble(d := room_script(r, rom))) != d], [])


class AssembleTestCase(TestCase):
    def test_labels_count_from_base(self) -> None:
        code, labels = assemble(["loop", op("wait", 1), op("jump", "loop")], base=0x20)
        self.assertEqual((code.hex(" "), labels), ("07 01 00 20 00", {"loop": 0x20}))

    def test_a_forward_text_label_lands_after_the_code(self) -> None:
        code, labels = assemble([op("say", "hi"), op("exit"), "hi", b"\xfd\xff"], base=0x30)
        self.assertEqual((code.hex(" "), labels["hi"]), ("26 34 00 ff fd ff", 0x34))

    def test_a_flag_jump_encodes_flag_then_target(self) -> None:
        self.assertEqual(encode(op("jump_if_flag", 7, 0x1234)), bytes([0x52, 0x07, 0x34, 0x12]))

    def test_a_decoded_instruction_encodes_back(self) -> None:
        raw = bytes([0x6E, 1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(encode(instruction(raw, 0)), raw)

    def test_operand_count_is_checked(self) -> None:
        with self.assertRaisesRegex(ValueError, "wait takes 1 operands"):
            op("wait")

    def test_a_byte_operand_cannot_be_a_label(self) -> None:
        with self.assertRaises(TypeError):
            op("wait", "later")

    def test_a_byte_operand_refuses_a_word(self) -> None:
        with self.assertRaisesRegex(ValueError, "1 byte"):
            encode(op("wait", 0x100))

    def test_a_label_defined_twice_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "twice"):
            assemble(["a", "a"], base=0)
