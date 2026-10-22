"""Japanese and French side by side, matched by ref: a room's texts, or the battle menu's and the inline strings.

python -m utils.compare 20                     # every text of dialog room 20
python -m utils.compare 20 0x512 0x500-0x540   # some refs
python -m utils.compare b12                    # battle room 12
python -m utils.compare all -g ペルソナ          # every dialog and battle room, texts whose JP or FR matches
python -m utils.compare inline -g STR --en     # the inline strings, DeJap's English as well where it exists
"""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

TEXT = Path("text")
FLAT = {"inline": ("jp/inline.xml", "inline.xml"), "battle": ("jp/battle.xml", "battle.xml")}


@dataclass(frozen=True)
class Row:
    source: str
    ref: int
    jp: str
    fr: str
    en: str = ""


def room_texts(path: Path) -> dict[int, str]:
    """ref -> data of a room file, every ref of a text pointing at it; an absent file reads empty."""
    if not path.exists():
        return {}
    texts: dict[int, str] = {}
    for text in ET.parse(path).getroot():
        data = text.findtext("data") or ""
        for ref in text.iterfind("refs/ref"):
            texts[int(ref.text or "", 0)] = data
    return texts


def flat_texts(path: Path) -> dict[int, str]:
    """ref -> text of inline.xml (a ref attribute) or battle.xml (refs like a room)."""
    root = ET.parse(path).getroot()
    if root.tag == "inline":
        return {int(string.attrib["ref"], 0): string.text or "" for string in root}
    texts: dict[int, str] = {}
    for string in root:
        for ref in string.iterfind("refs/ref"):
            texts[int(ref.text or "", 0)] = string.findtext("data") or ""
    return texts


def room_name(source: str) -> tuple[str, str]:
    """'20' -> ('dialog', '0020'), 'b12' -> ('battle', '0012')."""
    kind, number = ("battle", source[1:]) if source.startswith("b") else ("dialog", source)
    return kind, f"{int(number):04d}"


def room_rows(source: str, root: Path = TEXT) -> list[Row]:
    kind, name = room_name(source)
    jp, fr = room_texts(root / "jp" / kind / f"{name}.xml"), room_texts(root / "fr" / kind / f"{name}.xml")
    en = room_texts(root / "en" / kind / f"{name}.xml")
    return [
        Row(source, ref, jp.get(ref, ""), fr.get(ref, ""), en.get(ref, "")) for ref in sorted(jp.keys() | fr.keys())
    ]


def flat_rows(source: str, root: Path = TEXT) -> list[Row]:
    jp_file, fr_file = FLAT[source]
    jp, fr = flat_texts(root / jp_file), flat_texts(root / fr_file)
    return [Row(source, ref, jp.get(ref, ""), fr.get(ref, "")) for ref in sorted(jp.keys() | fr.keys())]


def all_rooms(root: Path = TEXT) -> list[str]:
    """Every dialog room then every battle room, as compare names them."""
    dialog = [str(int(path.stem)) for path in sorted((root / "jp" / "dialog").glob("*.xml"))]
    battle = [f"b{int(path.stem)}" for path in sorted((root / "jp" / "battle").glob("*.xml"))]
    return dialog + battle


def rows(source: str, root: Path = TEXT) -> list[Row]:
    if source == "all":
        return [row for room in all_rooms(root) for row in room_rows(room, root)]
    if source in FLAT:
        return flat_rows(source, root)
    return room_rows(source, root)


def parse_refs(specs: list[str]) -> set[int]:
    """'0x512', '0x500-0x540' -> the refs they name."""
    refs: set[int] = set()
    for spec in specs:
        first, _, last = spec.partition("-")
        refs.update(range(int(first, 0), int(last or first, 0) + 1))
    return refs


def select(found: list[Row], refs: set[int], pattern: str | None) -> list[Row]:
    regex = re.compile(pattern) if pattern else None
    return [
        row
        for row in found
        if (not refs or row.ref in refs) and (regex is None or regex.search(row.jp) or regex.search(row.fr))
    ]


def render(row: Row, english: bool, with_source: bool) -> str:
    def field(label: str, text: str) -> str:
        return f"{label}: " + text.strip("\n").replace("\n", "\n    ")

    head = f"=== {row.source} 0x{row.ref:x}" if with_source else f"=== 0x{row.ref:x}"
    lines = [head, field("JP", row.jp), field("FR", row.fr)]
    if english and row.en:
        lines.append(field("EN", row.en))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", help="dialog room (20), battle room (b12), all, inline or battle (the menu)")
    parser.add_argument("refs", nargs="*", help="refs or ranges: 0x512, 0x500-0x540")
    parser.add_argument("-g", "--grep", help="only texts whose Japanese or French matches this regex")
    parser.add_argument("--en", action="store_true", help="add DeJap's English (rooms only)")
    args = parser.parse_args()
    for row in select(rows(args.source), parse_refs(args.refs), args.grep):
        print(render(row, english=args.en, with_source=args.source == "all"))


if __name__ == "__main__":
    main()
