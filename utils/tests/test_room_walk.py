from pathlib import Path
from unittest import TestCase

from katsuji.script import Table

from utils.dump_rooms import get_dialog_room, is_compressed
from utils.vm.opcodes import Opcode, TextOpcode
from utils.vm.opcodes_map import opcode_names, opcode_table
from utils.vm.room_ops import OPERANDS, WIDTHS, decode
from utils.vm.room_walk import report, walk_room

root_dir = Path(__file__).parents[2]
RANDOM_BRANCH = 0x50

# A room with only a start-up script: jump_if_flag(5, 0x0A), end; dead wait_frames(1), end; display_text(0x0E), end.
ROOM = bytes.fromhex("0200 03050a00 ff 3f01ff 370e00 ff a0a1ff")


class OperandsTestCase(TestCase):
    def test_every_named_opcode_has_its_operands(self) -> None:
        self.assertEqual(set(OPERANDS), set(opcode_names))

    def test_the_layouts_agree_with_the_disassembler_sizes(self) -> None:
        for opcode, kinds in OPERANDS.items():
            handler = opcode_table.get(opcode)
            if not isinstance(handler, Opcode | TextOpcode) or set(kinds) & {"m", "l"}:
                continue
            with self.subTest(opcode=f"{opcode:02x}"):
                self.assertEqual(1 + sum(WIDTHS[kind] for kind in kinds), handler.size)

    def test_a_palette_preset_reads_all_its_ranges(self) -> None:
        self.assertEqual(decode(bytes.fromhex("51ff003412"), 0).data, ((0x1234, 0x1C2),))

    def test_a_motion_list_ends_on_fe(self) -> None:
        self.assertEqual(decode(bytes.fromhex("130312fe00"), 0).size, 4)


class WalkTestCase(TestCase):
    def test_the_walk_follows_the_branch_and_skips_the_dead_code(self) -> None:
        self.assertEqual(sorted(walk_room(ROOM).code), [0x02, 0x06, 0x0A, 0x0D])

    def test_the_text_counts_as_reached(self) -> None:
        self.assertEqual(walk_room(ROOM).unreached(), [(0x07, 0x0A)])

    def test_the_report_gives_the_dead_range_and_its_ops(self) -> None:
        self.assertEqual(
            report(1, walk_room(ROOM)),
            ["room   1: 14/17 bytes reached (82.4%), 4 ops", "  unreached 0007-0009 (3 bytes), decodes as 2 ops"],
        )

    def test_the_walk_reaches_what_the_disassembler_reaches(self) -> None:
        """Every opcode the room disassembler walked, the walk reaches too; the only exception is the FF the
        disassembler reads after a random_branch, which always jumps."""
        table = Table(str(root_dir / "text/table/jp.tbl"))
        with open(root_dir / "build/bl.sfc", "rb") as rom:
            for room_id in range(0xFF):
                if not is_compressed(rom, room_id):
                    continue
                with self.subTest(room=room_id):
                    room = get_dialog_room(rom, room_id, table, lang="jp", disasm=True)
                    walked = {
                        address
                        for address, (element, _comment, _size) in room.program._program.items()
                        if element[0] == "opcode" and address < len(room.data)
                    }
                    walk = walk_room(room.data)
                    self.assertEqual(walk.errors, [])
                    for address in walked - set(walk.code):
                        self.assertEqual(room.data[address], 0xFF)
                        self.assertTrue(
                            any(o + i.size == address for o, i in walk.code.items() if i.opcode == RANDOM_BRANCH)
                        )
