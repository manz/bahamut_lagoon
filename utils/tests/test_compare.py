import tempfile
from pathlib import Path
from unittest import TestCase

from utils.compare import Row, all_rooms, flat_rows, parse_refs, render, room_rows, select

ROOM = """<?xml version="1.0" ?>
<texts room_id="20" base="0x0">
    <text>
        <refs>
            <ref>0x512</ref>
            <ref>0x6f5</ref>
        </refs>
        <data>{}</data>
    </text>
</texts>
"""


class CompareTestCase(TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        for language, text in (("jp", "タイチョー"), ("fr", "Taicho"), ("en", "Taicho")):
            (self.root / language / "dialog").mkdir(parents=True)
            (self.root / language / "dialog" / "0020.xml").write_text(ROOM.format(text), encoding="utf-8")
        (self.root / "jp" / "inline.xml").write_text('<inline><string ref="0xeef26d">ＳＴＲ</string></inline>')
        (self.root / "inline.xml").write_text('<inline><string ref="0xeef26d">STR</string></inline>')

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_every_ref_of_a_text_is_a_row(self) -> None:
        self.assertEqual([row.ref for row in room_rows("20", self.root)], [0x512, 0x6F5])

    def test_a_row_pairs_the_languages(self) -> None:
        self.assertEqual(room_rows("20", self.root)[0], Row("20", 0x512, "タイチョー", "Taicho", "Taicho"))

    def test_an_absent_battle_room_reads_empty(self) -> None:
        self.assertEqual(room_rows("b20", self.root), [])

    def test_inline_strings_pair_by_ref(self) -> None:
        self.assertEqual(flat_rows("inline", self.root), [Row("inline", 0xEEF26D, "ＳＴＲ", "STR")])

    def test_all_names_the_dialog_rooms(self) -> None:
        self.assertEqual(all_rooms(self.root), ["20"])

    def test_a_range_names_its_refs(self) -> None:
        self.assertEqual(parse_refs(["0x10-0x12", "5"]), {0x10, 0x11, 0x12, 5})

    def test_grep_matches_either_language(self) -> None:
        self.assertEqual(len(select(room_rows("20", self.root), set(), "Taicho")), 2)

    def test_render_indents_continuation_lines(self) -> None:
        self.assertEqual(render(Row("20", 0x512, "a\nb", "c"), False, False), "=== 0x512\nJP: a\n    b\nFR: c")
