from io import StringIO
from unittest import TestCase, skipUnless

from utils.battle_walk import ROM, ROOMS, main, room_script, walk
from utils.vm.battle_script import OPS, header, instruction, size
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

    def test_the_report_totals_every_room(self) -> None:
        out = StringIO()
        main(["0"], echo=lambda line: print(line, file=out))
        self.assertIn("all: 1204/1204 code bytes reached", out.getvalue())
