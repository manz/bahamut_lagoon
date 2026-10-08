"""
Dialog text against the window it is drawn in, measured with katsuji in the dialogue font.

The field engine's window (`DA36AE`) is 32 tiles wide: a corner, 30 tiles, a corner. Text starts at column 1, so a
line holds 240 pixels. Lines go to a 256-pixel buffer and wrap nowhere: a longer line runs under the frame. Pages
turn by themselves once a window's lines are full (`DA3E1A`), so only the width matters: the build reflows each
paragraph to it.

A `[character][n]` prints name n of text/fr/names.xml (party members can be renamed, the default is measured), cut
to the 8 codes the engine copies (`DA3BDE`).
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
from katsuji.wrap import Controls, Wrapper
from script import Table

from utils.name_tables import read_names

KATSUJI_CONFIG = Path("katsuji.toml")
TABLE = Path("text/table/mz.tbl")
NAMES = Path("text/fr/names.xml")
DIALOGS = Path("text/fr/dialog")
LINE_WIDTH = 240  # 30 tiles between the frame's corners
NAME_CODES = 8
SPACE = 0xEF
NEWLINE = 0xFE
CHARACTER = re.compile(r"\[character\]\[0x([0-9a-fA-F]+)\]")
TERMINATORS = re.compile(r"\[end1?\]")
SPEAKER_LABEL = re.compile(r"[^ ].*:")  # "Yoyo:" or "[character][0x1]:" alone on its line
HEADING = re.compile(r"-[^ ].*-")  # "-Aller-": a heading the following lines explain
GLUED = re.compile(r"[?!;:»]")  # French puts a space before these: it must not break the line


def dialog_font(config_path: Path = KATSUJI_CONFIG) -> VwfFont:
    """The dialogue font as katsuji builds it from katsuji.toml."""
    font = katsuji_config.load(config_path).fonts["dialog"]
    atlas = Atlas.open(font.png, font.cell_width, font.cell_height, font.grid)
    return VwfFont.from_atlas(atlas, font.widths)


@dataclass(frozen=True)
class Overflow:
    room: str
    refs: str
    line: str
    width: int


class DialogLayout:
    """Measures dialog lines as the field engine draws them."""

    def __init__(self, table: Table, font: VwfFont, names: list[str], line_width: int = LINE_WIDTH) -> None:
        self.table = table
        self.wrapper = Wrapper([font], Controls(space=SPACE, newline=NEWLINE))
        self.names = [table.to_bytes(name.replace(" ", r"\s"))[:NAME_CODES] for name in names]
        self.line_width = line_width

    def encode(self, line: str) -> bytes:
        """The line's codes, names spelled out and terminators dropped."""
        codes = b""
        position = 0
        line = TERMINATORS.sub("", line)
        for match in CHARACTER.finditer(line):
            codes += self.table.to_bytes(line[position : match.start()].replace(" ", r"\s"))
            codes += self.names[int(match[1], 16)]
            position = match.end()
        return codes + self.table.to_bytes(line[position:].replace(" ", r"\s"))

    def width(self, line: str) -> int:
        return self.wrapper.measure(self.encode(line))

    def reflow(self, text: str) -> str:
        """`text` laid out to the window: each paragraph's lines joined and wrapped again.

        Kept as written: blank lines (they separate paragraphs), lines starting with a space (centred cards,
        choices), a speaker label or a -heading- alone on its line, and texts ending in [end1] (a choice follows
        them)."""
        if text.endswith("[end1]"):
            return text
        out: list[str] = []
        paragraph: list[str] = []
        for line in text.split("\n"):
            if not line or line.startswith(" ") or SPEAKER_LABEL.fullmatch(line) or HEADING.fullmatch(line):
                if paragraph:
                    out.append(self._wrap_line(" ".join(paragraph)))
                    paragraph = []
                out.append(line)
            else:
                paragraph.append(line)
        if paragraph:
            out.append(self._wrap_line(" ".join(paragraph)))
        return "\n".join(out)

    def _wrap_line(self, line: str) -> str:
        """`line` broken at spaces, katsuji's way: a word that would pass the width starts a new line."""
        lines: list[str] = []
        current = ""
        words: list[str] = []
        for word in line.split(" "):
            if words and GLUED.match(word):
                words[-1] += f" {word}"
            else:
                words.append(word)
        for word in words:
            candidate = f"{current} {word}" if current else word
            if current and self.width(candidate) > self.line_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
        return "\n".join(lines)

    def overflows(self, text: str) -> Iterator[tuple[str, int]]:
        """The lines of `text` wider than the window, with their width."""
        for line in text.split("\n"):
            width = self.width(line)
            if width > self.line_width:
                yield line, width


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
