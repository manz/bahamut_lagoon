import os
from unittest.case import TestCase

from script import Table

from utils.dump_rooms import get_dialog_room
from utils.vm.room import prettify

root_dir = os.path.join(os.path.dirname(__file__), '../..')


class DialogTestCase(TestCase):
    def setUp(self):
        self.table = Table(os.path.join(root_dir, './text/table/jp.tbl'))

    def test_get_room_0(self):
        with open(os.path.join(root_dir, 'bl.sfc'), 'rb') as rom:
            room = get_dialog_room(rom, 0, self.table, lang='jp', disasm=True)
            self.assertEqual(room.id, 0)
            self.assertIsNotNone(room.room)
            texts = room.dump_text()

            yes_no_text = texts.find('text')
            yes_no_text_data = yes_no_text.find('data')
            yes_no_text_refs = yes_no_text.find('refs')

            self.assertEqual(yes_no_text_data.text, ' はい\n いいえ[end1]')
            self.assertEqual(int(yes_no_text_refs[0].text, 16), 0x9fb)
