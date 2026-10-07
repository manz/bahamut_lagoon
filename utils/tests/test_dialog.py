import io
import os
from unittest.case import TestCase

from a816.writers import IPSWriter
from script import Table

from utils.cartridge import rom_offset
from utils.dump_rooms import build_text_patch, get_dialog_room

root_dir = os.path.join(os.path.dirname(__file__), "../..")


class DialogTestCase(TestCase):
    def setUp(self):
        self.table = Table(os.path.join(root_dir, "./text/table/jp.tbl"))

    def test_get_room_0(self):
        with open(os.path.join(root_dir, "build/bl.sfc"), "rb") as rom:
            room = get_dialog_room(rom, 0, self.table, lang="jp", disasm=True)
            self.assertEqual(room.id, 0)
            self.assertIsNotNone(room.room)
            texts = room.dump_text()

            yes_no_text = texts.find("text")
            yes_no_text_data = yes_no_text.find("data")
            yes_no_text_refs = yes_no_text.find("refs")

            self.assertEqual(yes_no_text_data.text, " はい\n いいえ[end1]")
            self.assertEqual(int(yes_no_text_refs[0].text, 16), 0x9FB)

    def test_text_patch_returns_the_end_of_the_relocated_rooms(self):
        # A room too big for the RAM buffer is stored uncompressed, which patches the compression flags; the battle
        # rooms are packed right after the returned address, so it must not be one of those flag addresses.
        start = rom_offset(0xF00000)
        table = Table(os.path.join(root_dir, "./text/table/mz.tbl"))
        with open(os.path.join(root_dir, "build/bl.sfc"), "rb") as rom:
            end = build_text_patch(rom, table, IPSWriter(io.BytesIO()), start)
        self.assertGreater(end, start)
