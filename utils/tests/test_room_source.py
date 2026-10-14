import os
import tempfile
from pathlib import Path
from unittest import TestCase

from script import Table

from utils.dump_rooms import get_dialog_room, is_compressed
from utils.room_source import MACROS, NO_MACRO, assemble_room, read_macros, room_source

root_dir = Path(__file__).parents[2]


class ReadMacrosTestCase(TestCase):
    def test_a_macro_is_keyed_by_its_opcode_with_its_operand_widths(self) -> None:
        source = '.macro jump(address) {\n    """Room opcode 0x00: jump."""\n    .db 0x00\n    .dw address\n}\n'
        macro = read_macros(source)[0x00]
        self.assertEqual((macro.name, macro.widths, macro.size), ("jump", (2,), 3))

    def test_a_signature_over_several_lines_is_read(self) -> None:
        source = ".macro wide(\n    param1,\n    param2,\n) {\n    .db 0x5B, param1, param2\n}\n"
        self.assertEqual(read_macros(source)[0x5B].widths, (1, 1))

    def test_every_opcode_has_a_macro(self) -> None:
        self.assertEqual(len(read_macros((root_dir / MACROS).read_text(encoding="utf-8"))), 150)


class RoomRoundTripTestCase(TestCase):
    def test_every_dialog_room_assembles_back_to_its_bytes(self) -> None:
        """Each compressed room, disassembled to macro source and assembled with a816, gives its bytes back, every
        opcode the walk reached written as its macro."""
        macros = read_macros((root_dir / MACROS).read_text(encoding="utf-8"))
        table = Table(os.path.join(root_dir, "text/table/jp.tbl"))
        with open(root_dir / "build/bl.sfc", "rb") as rom, tempfile.TemporaryDirectory() as work:
            for room_id in range(0xFF):
                if not is_compressed(rom, room_id):
                    continue
                with self.subTest(room=room_id):
                    room = get_dialog_room(rom, room_id, table, lang="jp", disasm=True)
                    source = Path(work) / f"{room_id:03}.s"
                    text = room_source(room, macros)
                    self.assertNotIn(NO_MACRO, text)
                    source.write_text(text, encoding="utf-8")
                    assembled = Path(work) / f"{room_id:03}.bin"
                    self.assertEqual(assemble_room(source, assembled, Path(work) / "obj"), [])
                    self.assertEqual(assembled.read_bytes(), room.data)
