"""Every character of the French script has a code and a dialogue glyph: the table encodes one it lacks as nothing,
and a code with a blank cell prints nothing, so the game would silently drop it (« cœur » printed « cur »)."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import TestCase

from katsuji import png
from katsuji.png import Pixels
from katsuji.script import Table

ROOT = Path(__file__).parents[2]
SCRIPTS = ROOT / "text/fr"
TABLE = ROOT / "text/table/mz.tbl"
DIALOG_FONT = ROOT / "fonts/fft.png"  # 16 cells of 8x16 a row, by code
CODES = re.compile(r"\[[^\]]*\]|``")  # control codes, and the opening quote pair the table encodes as one


def script_characters() -> dict[str, str]:
    """character -> the first file:ref using it, over every dialog and battle room text."""
    characters: dict[str, str] = {}
    for path in sorted([*SCRIPTS.glob("dialog/*.xml"), *SCRIPTS.glob("battle/*.xml")]):
        for text in ET.parse(path).getroot():
            where = f"{path.parent.name}/{path.name}:{text.findtext('refs/ref')}"
            for character in set(CODES.sub("", text.findtext("data") or "")) - {" ", "\n"}:
                characters.setdefault(character, where)
    return characters


def has_ink(font: Pixels, code: int) -> bool:
    x, y = code % 16 * 8, code // 16 * 16
    return bool(font[y : y + 16, x : x + 8].any())


class ScriptEncodingTestCase(TestCase):
    characters = script_characters()
    table = Table(str(TABLE))

    def test_every_character_has_a_code(self) -> None:
        self.assertEqual({c: where for c, where in self.characters.items() if not self.table.to_bytes(c)}, {})

    def test_every_character_has_a_glyph(self) -> None:
        font = png.read(DIALOG_FONT)[0]
        blank = {
            c: where
            for c, where in self.characters.items()
            if (codes := bytes(self.table.to_bytes(c))) and len(codes) == 1 and not has_ink(font, codes[0])
        }
        self.assertEqual(blank, {})

    def test_digits_are_written_as_digits(self) -> None:
        # a [0x..] reads as a closing tag to the centring, which drops the space before it ("Chapitre[0xb6]")
        codes = {f"[{code:#04x}]" for code in self.table.to_bytes("0123456789")}
        written = re.compile(r"(?<!\[0xf[0-9a-f]\])(\[0x[0-9a-f]{2}\])")
        found = {
            f"{path.name}: {code}"
            for path in SCRIPTS.glob("*/*.xml")
            for code in written.findall(path.read_text(encoding="utf-8"))
            if code in codes
        }
        self.assertEqual(found, set())
