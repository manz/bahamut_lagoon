"""
Dialog text against the window it is drawn in, measured with katsuji in the dialogue font.

The field engine's window (`DA36AE`) is 32 tiles wide: a corner, 30 tiles, a corner. Text starts at column 1, so a
line holds 240 pixels. Lines go to a 256-pixel buffer and wrap nowhere: a longer line runs under the frame. Pages
turn by themselves once a window's lines are full (`DA3E1A`), so only the width matters: the build reflows each
paragraph to it, with katsuji's TextLayout in French typography.

A `[character][n]` prints a name cut to the 8 codes the engine copies (`DA3BDE`). Names 0-9 come from the party
records at 7E2B00, which the player renames: they are measured as 8 of the widest letter one could type. The others
are fixed, measured as text/fr/names.xml spells them.
"""

import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from katsuji import config as katsuji_config
from katsuji.atlas import Atlas
from katsuji.formats import VwfFont
from katsuji.layout import TextLayout
from katsuji.typeset import FRENCH, Markup
from katsuji.typeset import typeset as katsuji_typeset
from katsuji.wrap import Controls, Wrapper
from script import Table

from utils.name_tables import read_names

KATSUJI_CONFIG = Path("katsuji.toml")
TABLE = Path("text/table/mz.tbl")
NAMES = Path("text/fr/names.xml")
DIALOGS = Path("text/fr/dialog")
LINE_WIDTH = 240  # 30 tiles between the frame's corners
NAME_CODES = 8
RENAMEABLE = 0x0A  # names below this come from the party records (7E2B00), the player's choice
NAME_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÀÂÇÈÉÊËÎÏÔÙÛàâçèéêëîïôùû"
SPACE = 0xEF
NEWLINE = 0xFE
CHARACTER = re.compile(r"\[character\]\[0x([0-9a-fA-F]+)\]")
TERMINATORS = re.compile(r"\[end1?\]")
SPEAKER_LABEL = re.compile(r"[^ ].*:")  # "Yoyo:" or "[character][0x1]:" alone on its line
HEADING = re.compile(r"-[^ ].*-")  # "-Aller-": a heading the following lines explain
LIST_ITEM = re.compile(r"(\d+|\[0x(af|b[0-8])\])+ ?[-.)]")  # "1- ", "[0xb0]- ": an item, a line of its own
MARKUP = Markup(
    tag=r"\[character\]\[0x[0-9a-f]+\]|\[[^\]]*\]",  # a name, a glyph ([0xd8]) or a control ([end])
    words=r"\[character\].*",  # a name reads as a word: "[character][0x0] !"
    glyphs=r"\[0x[0-9a-f]+\]",  # a glyph keeps what follows it tight: "[0xd8]!"
    speakers=True,  # no space before the colon of "Roi de Kana:" opening a line
)


def dialog_font(config_path: Path = KATSUJI_CONFIG) -> VwfFont:
    """The dialogue font as katsuji builds it from katsuji.toml."""
    font = katsuji_config.load(config_path).fonts["dialog"]
    atlas = Atlas.open(font.png, font.cell_width, font.cell_height, font.grid)
    return VwfFont.from_atlas(atlas, font.widths)


def typeset(text: str) -> str:
    """`text` in French typography, the game's tags kept as they are."""
    return katsuji_typeset(text, FRENCH, MARKUP)


@dataclass(frozen=True)
class Overflow:
    room: str
    refs: str
    line: str
    width: int


class DialogLayout:
    """Measures dialog lines as the field engine draws them, and lays them out with katsuji."""

    def __init__(self, table: Table, font: VwfFont, names: list[str], line_width: int = LINE_WIDTH) -> None:
        self.table = table
        self.wrapper = Wrapper([font], Controls(space=SPACE, newline=NEWLINE))
        self.names = [table.to_bytes(name.replace(" ", r"\s"))[:NAME_CODES] for name in names]
        self.default_names = list(self.names)
        widest = max(NAME_LETTERS, key=lambda letter: self.wrapper.measure(table.to_bytes(letter)))
        self.names[:RENAMEABLE] = [table.to_bytes(widest * NAME_CODES)] * RENAMEABLE
        self.line_width = line_width
        self.layout = TextLayout(
            self.width,
            line_width,
            FRENCH,
            MARKUP,
            labels=SPEAKER_LABEL.pattern,
            headings=HEADING.pattern,
            items=LIST_ITEM.pattern,
            placed_measure=self.default_width,
            min_balanced_width=line_width * 2 // 3,
        )

    def encode(self, line: str, names: list[bytes] | None = None) -> bytes:
        """The line's codes, names spelled out (at their widest unless `names` says) and terminators dropped."""
        names = self.names if names is None else names
        codes = b""
        position = 0
        line = TERMINATORS.sub("", line)
        for match in CHARACTER.finditer(line):
            codes += self.table.to_bytes(line[position : match.start()].replace(" ", r"\s"))
            codes += names[int(match[1], 16)]
            position = match.end()
        return codes + self.table.to_bytes(line[position:].replace(" ", r"\s"))

    def width(self, line: str) -> int:
        return self.wrapper.measure(self.encode(line))

    def default_width(self, line: str) -> int:
        """`line`'s width with every name at its default spelling: where it sits, not how wide it may grow."""
        return self.wrapper.measure(self.encode(line, self.default_names))

    def reflow(self, text: str, page_lines: int | None = None, keep_lines: bool = False) -> str:
        """`text` typeset and laid out to the window (katsuji's TextLayout: paragraphs reflowed by sentences, lines
        placed, blocks kept within a window of `page_lines`). A text ending in [end1] (a choice follows it), or given
        `keep_lines` (a choice's prompt, its options a line each), is typeset only."""
        if keep_lines or text.endswith("[end1]"):
            return typeset(text)
        return self.layout.reflow(text, page_lines)

    def place(self, line: str) -> str:
        return self.layout.place(line)

    def centre(self, line: str) -> str:
        return self.layout.centre(line)

    def overflows(self, text: str) -> Iterator[tuple[str, int]]:
        return self.layout.overflows(text)


def default_layout() -> DialogLayout:
    return DialogLayout(Table(str(TABLE)), dialog_font(), read_names(NAMES))


def script_overflows(layout: DialogLayout, dialogs: Path = DIALOGS) -> Iterator[Overflow]:
    """Lines still wider than the window once reflowed: kept lines (cards, choices) and words too long to break."""
    for path in sorted(dialogs.glob("*.xml")):
        for text in ET.parse(path).getroot():
            refs = " ".join(ref.text or "" for ref in text.iter("ref"))
            for line, width in layout.overflows(layout.reflow(text.findtext("data") or "")):
                yield Overflow(path.stem, refs, line, width)


def main() -> int:
    overflows = list(script_overflows(default_layout()))
    for overflow in overflows:
        print(f"{overflow.room} [{overflow.refs}] {overflow.width}px: {overflow.line}")
    print(f"{len(overflows)} line(s) wider than {LINE_WIDTH} pixels")
    return 1 if overflows else 0


if __name__ == "__main__":
    sys.exit(main())
