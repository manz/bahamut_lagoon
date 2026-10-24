"""The glossary's wording rules (docs/glossary.md, "Open questions, decided") checked over every French script text:
the calques the stiffness review found, kept from coming back."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import TestCase

SCRIPTS = Path(__file__).parents[2] / "text/fr"

# rule -> the wording it forbids
FORBIDDEN = {
    "アニキ is Byuu, not grand frère": re.compile(r"Byuu,? grand frère|grand frère,? Byuu", re.IGNORECASE),
    "ビュウ隊長 called out is Capitaine": re.compile(r"Capitaine Byuu", re.IGNORECASE),
    "ね is a question or a statement": re.compile(r"n'est-ce pas\.+(?![.\s]*\?)"),
    "no affirmatif on a question": re.compile(r"affirmatif\s*\?"),
    "ごくろうさま by the situation": re.compile(r"merci pour (?:ta|votre) peine|tu as bien travaillé", re.IGNORECASE),
    "〜屋です is Bienvenue au": re.compile(r"Ici (?:le magasin|la boutique)"),
    "奇跡の大陸 is le continent des miracles": re.compile(r"Continent\s+Miracle"),
    "救世軍 is l'Armée du salut": re.compile(r"Armée de Libération d'Orelus"),
    "a set phrase takes its French": re.compile(
        r"C'est grave !|Ça me rappelle tant de souvenirs|sentiments partagés|ne sont pas rien|c'est soudain, mais"
        r"|Je t'en prie, je t'en prie|transmise à Kana|(?:apprendre|appris) le c(?:œ|oe)ur",
        re.IGNORECASE,
    ),
    "a calqued noun takes a pronoun or its French": re.compile(
        r"cette personne|fille humaine|révolution de la liberté|Empereur de l'Empire", re.IGNORECASE
    ),
    "a pause is one ellipsis": re.compile(r"(?<=[^\s.\]])\.\.\. \.\.\.(?=[^\s.])"),
}


def script_texts() -> list[tuple[str, str]]:
    """(file:first ref, data) of every dialog and battle room text."""
    texts = []
    for path in sorted([*SCRIPTS.glob("dialog/*.xml"), *SCRIPTS.glob("battle/*.xml")]):
        for text in ET.parse(path).getroot():
            where = f"{path.parent.name}/{path.name}:{text.findtext('refs/ref')}"
            texts.append((where, text.findtext("data") or ""))
    return texts


class GlossaryRulesTestCase(TestCase):
    texts = script_texts()

    def test_no_forbidden_wording(self) -> None:
        for rule, pattern in FORBIDDEN.items():
            with self.subTest(rule):
                self.assertEqual([where for where, data in self.texts if pattern.search(data)], [])

    def test_affirmatif_once_a_speech_at_most(self) -> None:
        self.assertEqual([where for where, data in self.texts if data.count("affirmatif") > 1], [])
