from pathlib import Path
from unittest import TestCase

from utils.dump_rooms import is_compressed
from utils.vm.room_asm import Op, assemble, encode, op
from utils.vm.room_ops import decode
from utils.vm.room_script import Data, disassemble, listing
from utils.vm.room_walk import ROOMS, room_data, walk_room

root_dir = Path(__file__).parents[2]

# A room with only a start-up script: jump_if_flag(5, 0x0A), end; dead wait_frames(1), end; display_text(0x0E), end.
ROOM = bytes.fromhex("0200 03050a00 ff 3f01ff 370e00 ff a0a1ff")


def reencoded(data: bytes) -> bytes:
    return b"".join(item.raw if isinstance(item, Data) else encode(item) for item in disassemble(walk_room(data)))


class ReencodeTestCase(TestCase):
    def test_every_room_reencodes_to_its_bytes(self) -> None:
        mismatched, rooms = [], 0
        with open(root_dir / "build/bl.sfc", "rb") as rom:
            for room in range(ROOMS):
                if not is_compressed(rom, room):
                    continue
                data = room_data(rom, room)
                assert data is not None
                rooms += 1
                if reencoded(data) != data:
                    mismatched.append(room)
        self.assertEqual((rooms, mismatched), (83, []))

    def test_every_instruction_encodes_to_its_own_bytes(self) -> None:
        """Data is copied as it is: the instructions alone, each against its slice."""
        with open(root_dir / "build/bl.sfc", "rb") as rom:
            for room in range(ROOMS):
                data = room_data(rom, room)
                if data is None:
                    continue
                code = walk_room(data).code.values()
                with self.subTest(room=room):
                    self.assertEqual([i.offset for i in code if encode(i) != data[i.offset : i.offset + i.size]], [])


class AssembleTestCase(TestCase):
    def test_jumps_resolve_labels_from_the_room_start(self) -> None:
        code, labels = assemble(["loop", op("wait_frames", 1), op("jump_if_flag", 0x10, "loop"), op("exit")], 0x40)
        self.assertEqual((code.hex(" "), labels), ("3f 01 03 10 40 00 ff", {"loop": 0x40}))

    def test_labels_after_code_count_its_size(self) -> None:
        code, labels = assemble([op("display_text", "text"), op("exit"), "text", b"\x20\xff"], 0x10)
        self.assertEqual((code.hex(" "), labels["text"]), ("37 14 00 ff 20 ff", 0x14))

    def test_a_list_gets_its_end(self) -> None:
        self.assertEqual(encode(op("actor_move", 3, [0x20])).hex(" "), "13 03 20 ff")

    def test_a_motion_list_may_end_on_fe(self) -> None:
        self.assertEqual(encode(op("actor_move", 3, [0x20, 0xFE])).hex(" "), "13 03 20 fe")

    def test_words_and_long_addresses_are_little_endian(self) -> None:
        self.assertEqual(encode(op("copy_byte", 0x7E0312, 0x7E3BD0)).hex(" "), "59 12 03 7e d0 3b 7e")

    def test_the_operand_count_is_checked(self) -> None:
        with self.assertRaisesRegex(ValueError, "wait_frames takes 1 operands"):
            op("wait_frames")

    def test_a_byte_operand_takes_no_label(self) -> None:
        with self.assertRaisesRegex(TypeError, "cannot take the label"):
            encode(op("set_flag", "flag"), {"flag": 1})

    def test_a_list_without_its_end_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "lacks its end"):
            encode(Op(0x14, (b"\x01",)))

    def test_assembled_code_decodes_back(self) -> None:
        code, _ = assemble([op("actor_place", 1, 2, 3), op("actors_hold", [1, 2])], 0)
        self.assertEqual([decode(code, 0).name, decode(code, 4).operands], ["actor_place", (b"\x01\x02\xff",)])


class ListingTestCase(TestCase):
    def test_the_items_cover_the_room_once(self) -> None:
        items = disassemble(walk_room(ROOM))
        self.assertEqual(
            [(i.offset, i.kind if isinstance(i, Data) else i.name) for i in items],
            [(0, "data"), (2, "jump_if_flag"), (6, "exit"), (7, "unreached"), (0x0A, "display_text"), (0x0D, "exit"),
             (0x0E, "text")],
        )  # fmt: skip

    def test_the_listing_labels_targets_and_shows_texts(self) -> None:
        self.assertEqual(
            listing(ROOM, lambda raw: raw.hex(), show_bytes=True),
            [
                "; 0x11 bytes, header 0x2, 4 instructions",
                "; +0 start-up: L0002",
                "  0000  db 02 00",
                "",
                "L0002:  ; +0 start-up",
                "  0002 03 05 0a 00               jump_if_flag 0x05, L000a",
                "  0006 ff                        exit",
                "  0007  db 3f 01 ff  ; unreached",
                "",
                "L000a:",
                "  000a 37 0e 00                  display_text T000e  ; a0a1ff",
                "  000d ff                        exit",
                "",
                "T000e:",
                "  000e  text a0a1ff",
            ],
        )
