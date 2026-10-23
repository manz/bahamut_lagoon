from io import StringIO
from unittest import TestCase, skipUnless

from utils.battle_walk import IPS, ROM, ROOMS, fr_rom, main, room_script, walk
from utils.vm.battle_script import OPS, TEXTS, TextCodec, disassemble, header, instruction, size
from utils.vm.battle_script import main as listing_main
from utils.vm.opcodes_map import battle_opcode_names, battle_opcode_table


class InstructionTestCase(TestCase):
    def test_a_conditional_jump_has_its_flag_then_its_target(self) -> None:
        ins = instruction(bytes([0x52, 0x07, 0x34, 0x12]), 0)
        self.assertEqual((ins.name, ins.args, ins.size, ins.targets), ("jump_if_flag", (7, 0x1234), 4, [0x1234]))

    def test_the_scripted_action_takes_seven_bytes(self) -> None:
        self.assertEqual(size(0x6E), 8)

    def test_an_unused_opcode_is_one_byte(self) -> None:
        self.assertEqual((instruction(b"\x2d", 0).name, size(0x2D)), ("unused_2d", 1))

    def test_say_points_at_its_text(self) -> None:
        self.assertEqual(instruction(bytes([0x26, 0xDA, 0x04]), 0).text, 0x4DA)

    def test_the_room_walk_table_follows_the_sizes(self) -> None:
        self.assertEqual({op: battle_opcode_names[op] for op in OPS}, {op: name for op, (name, _) in OPS.items()})
        self.assertEqual(getattr(battle_opcode_table[0x31], "size", None), size(0x31))


@skipUnless(ROM.exists(), "needs build/bl.sfc")
class RoomWalkTestCase(TestCase):
    def test_every_room_reaches_only_known_opcodes(self) -> None:
        for room_id in range(ROOMS):
            with self.subTest(room=room_id):
                self.assertEqual([i for i in walk(room_script(room_id)).code.values() if i.op not in OPS], [])

    def test_the_walk_covers_the_code_but_dead_bytes(self) -> None:
        """Only the dead exits after an exit / return and one skipped byte in room 15 stay unreached."""
        unreached = sum(hi - lo for r in range(ROOMS) for lo, hi in walk(room_script(r)).unreached())
        self.assertEqual(unreached, 6)

    def test_room_0_opens_on_its_turn_entries(self) -> None:
        data = room_script(0)
        self.assertEqual(header(data).entries[:3], (0x20, 0x23, 0x24))

    @skipUnless(IPS.exists(), "needs build/bl.ips")
    def test_the_french_build_only_moves_texts(self) -> None:
        """Same instructions at the same offsets in every room; only the text addresses differ."""
        changed = []
        for room_id in range(ROOMS):
            vanilla, french = walk(room_script(room_id)).code, walk(room_script(room_id, fr_rom())).code
            changed += [
                (room_id, at)
                for at in vanilla.keys() | french.keys()
                if at not in vanilla
                or at not in french
                or vanilla[at].op != french[at].op
                or (vanilla[at].args != french[at].args and vanilla[at].name not in TEXTS)
            ]
        self.assertEqual(changed, [])

    def test_the_report_totals_every_room(self) -> None:
        out = StringIO()
        main(["0"], echo=lambda line: print(line, file=out))
        self.assertIn("all: 1204/1204 code bytes reached", out.getvalue())


class TextCodecTestCase(TestCase):
    def test_vanilla_text_keeps_its_page_across_characters(self) -> None:
        codec = TextCodec.for_rom(french=False)
        self.assertEqual(codec.decode(bytes([0xF0, 0x00, 0x00, 0xFE, 0xFD, 0xFF]), 0), "ヴヴ\\n[wait]")

    def test_a_control_code_shows_its_argument(self) -> None:
        codec = TextCodec.for_rom(french=True)
        self.assertEqual(codec.decode(bytes([0xFC, 0x28, 0xF9, 0x01, 0x02, 0xFF, 0x00]), 0), "[fc 28][f9 01 02]")


@skipUnless(ROM.exists(), "needs build/bl.sfc")
class ListingTestCase(TestCase):
    def listing(self, *argv: str) -> list[str]:
        out: list[str] = []
        listing_main(list(argv), echo=out.append)
        return out

    def test_entries_are_named_by_when_they_run(self) -> None:
        self.assertIn("  0000  entry 00 -> turn_start", "\n".join(self.listing("0")))

    def test_jump_targets_get_labels(self) -> None:
        out = self.listing("0")
        self.assertEqual(("  0025  jump_if_flag 0x00, L_00a9" in out, "L_00a9:" in out), (True, True))

    def test_bytes_show_each_instruction(self) -> None:
        self.assertIn("  0020 f4 84                     set_room_flag 0x84", self.listing("0", "--bytes"))

    def test_area_records_are_decoded(self) -> None:
        self.assertIn("  023e  area x=0x02, y=0x11, w=0x06, h=0x01  ; set local flag 0x00", self.listing("6"))

    @skipUnless(IPS.exists(), "needs build/bl.ips")
    def test_the_french_build_shows_french_text(self) -> None:
        say = next(line for line in self.listing("0", "--fr") if line.startswith("  0063  say"))
        self.assertIn('"[f4 0b]: Hmm !![fc 28]', say)

    def test_the_disassembly_covers_the_whole_script(self) -> None:
        data = room_script(15)
        dis = disassemble(data)
        last_at, last = dis.items[-1]
        self.assertEqual((dis.items[0][0], last_at + len(getattr(last, "raw", b""))), (0x20, len(data)))
