"""Every character of the French script has a code: the table encodes one it lacks as nothing, so the game would
silently drop it (« cœur » printed « cur »)."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import TestCase

from katsuji.script import Table

ROOT = Path(__file__).parents[2]
SCRIPTS = ROOT / "text/fr"
TABLE = ROOT / "text/table/mz.tbl"
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


class ScriptEncodingTestCase(TestCase):
    def test_every_character_has_a_code(self) -> None:
        table = Table(str(TABLE))
        self.assertEqual({c: where for c, where in script_characters().items() if not table.to_bytes(c)}, {})
