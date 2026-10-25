"""Every character of the French script has a code and a dialogue glyph: the table encodes one it lacks as nothing,
and a code with a blank cell prints nothing, so the game would silently drop it (« cœur » printed « cur »)."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import TestCase

from katsuji.script import Table
from PIL import Image

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


def has_ink(font: Image.Image, code: int) -> bool:
    x, y = code % 16 * 8, code // 16 * 16
    return any(font.getpixel((x + i, y + j)) for i in range(8) for j in range(16))


class ScriptEncodingTestCase(TestCase):
    characters = script_characters()
    table = Table(str(TABLE))

    def test_every_character_has_a_code(self) -> None:
        self.assertEqual({c: where for c, where in self.characters.items() if not self.table.to_bytes(c)}, {})

    def test_every_character_has_a_glyph(self) -> None:
        font = Image.open(DIALOG_FONT)
        blank = {
            c: where
            for c, where in self.characters.items()
            if (codes := bytes(self.table.to_bytes(c))) and len(codes) == 1 and not has_ink(font, codes[0])
        }
        self.assertEqual(blank, {})
