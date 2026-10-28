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
from katsuji.formats import VwfFont
from katsuji.layout import TextLayout
from katsuji.script import Table
from katsuji.typeset import FRENCH, Markup
from katsuji.typeset import typeset as katsuji_typeset
from katsuji.wrap import Controls, Wrapper

from utils.name_tables import read_names, referenced_names

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
OPTION = re.compile(r"^ +(?=\S)", re.MULTILINE)  # a choice's option: one of its last lines, opening on a space
OPTION_INDENT = "  "  # two spaces, 10 pixels: the options stand clear of the cursor
TRAILING_TAGS = re.compile(r"(.*?)((?:\[[^\]]*\])*)", re.DOTALL)  # a line's words, then the tags closing it
LEFT, CENTER, STEPS = "left", "center", "steps"  # a <text>'s align: as reflowed, centred, or stepped like stairs
STEP = "  "  # 10 pixels: how much further in each line of a stepped block starts
CENTRE_MARK = "  "  # katsuji centres a line set two spaces in
FINE_SPACES = 0xD9  # blank glyphs advancing 1 to 7 pixels (katsuji.toml): an indent's last pixels, finer than a space
LIST_ITEM = re.compile(r"(\d+|\[0x(af|b[0-8])\])+ ?[-.)]")  # "1- ", "[0xb0]- ": an item, a line of its own
MARKUP = Markup(
    tag=r"\[character\]\[0x[0-9a-f]+\]|\[[^\]]*\]",  # a name, a glyph ([0xd8]) or a control ([end])
    words=r"\[character\].*",  # a name reads as a word: "[character][0x0] !"
    glyphs=r"\[0x[0-9a-f]+\]",  # a glyph keeps what follows it tight: "[0xd8]!"
    speakers=True,  # no space before the colon of "Roi de Kana:" opening a line
)


def dialog_font(config_path: Path = KATSUJI_CONFIG) -> VwfFont:
    """The dialogue font katsuji built from katsuji.toml (`katsuji build`, or build.py, which runs it first)."""
    return VwfFont.decode(katsuji_config.load(config_path).fonts["dialog"].output.read_bytes())


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
        written = sorted(referenced_names(names).items(), key=lambda entry: -len(entry[1]))
        self.written_names = {name: index for index, name in written}  # the build encodes these as their reference
        self.name_pattern = re.compile(
            "|".join([CHARACTER.pattern, *(f"(?P<w{index}>{re.escape(name)})" for index, name in written)])
        )
        self.default_names = list(self.names)
        widest = max(NAME_LETTERS, key=lambda letter: self.wrapper.measure(table.to_bytes(letter)))
        self.names[:RENAMEABLE] = [table.to_bytes(widest * NAME_CODES)] * RENAMEABLE
        self.line_width = line_width
        self.space_width = self.wrapper.measure(bytes([SPACE]))
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
            blank_ends_window=True,  # pages turn once a window is full (DA3E1A): a blank line ends its window
        )

    def encode(self, line: str, names: list[bytes] | None = None) -> bytes:
        """The line's codes, names spelled out (at their widest unless `names` says) and terminators dropped."""
        names = self.names if names is None else names
        codes = b""
        position = 0
        line = TERMINATORS.sub("", line)
        for match in self.name_pattern.finditer(line):
            codes += self.table.to_bytes(line[position : match.start()].replace(" ", r"\s"))
            index = int(match[1], 16) if match[1] else self.written_names[match[0]]
            codes += names[index]
            position = match.end()
        return codes + self.table.to_bytes(line[position:].replace(" ", r"\s"))

    def width(self, line: str) -> int:
        return self.wrapper.measure(self.encode(line))

    def default_width(self, line: str) -> int:
        """`line`'s width with every name at its default spelling: where it sits, not how wide it may grow."""
        return self.wrapper.measure(self.encode(line, self.default_names))

    def reflow(self, text: str, page_lines: int | None = None, choice: bool = False, align: str = LEFT) -> str:
        """`text` typeset and laid out to the window (katsuji's TextLayout: paragraphs reflowed by sentences, lines
        placed, blocks kept within a window of `page_lines`). A `choice`'s prompt is reflowed so, its options kept a line
        each; aligned CENTER, each line is centred, and aligned STEPS, each line of a block is set a STEP further in than
        the one before."""
        if choice:
            return self.choice(text, page_lines)
        if align == CENTER:
            return self.centred(text)
        if align == STEPS:
            return stepped(text)
        return self.layout.reflow(text, page_lines)

    def choice(self, text: str, page_lines: int | None = None) -> str:
        """A choice's text: its prompt reflowed, then the blank lines before its options as written, then the options
        (its last lines, each opening on a space) a line each, set OPTION_INDENT in."""
        lines = text.split("\n")
        options = len(lines)
        while options and OPTION.match(lines[options - 1]):
            options -= 1
        gap = options
        while gap and not lines[gap - 1].strip(" "):
            gap -= 1
        prompt = self.layout.reflow("\n".join(lines[:gap]), page_lines) if gap else None
        if prompt is not None and page_lines:
            # the cursor walks the window's lines from the top: the options open a page, as in the Japanese
            gap = options
            prompt += "\n" * (-len(prompt.split("\n")) % page_lines)
        rest = typeset(OPTION.sub(OPTION_INDENT, "\n".join(lines[gap:]))) if gap < len(lines) else None
        return "\n".join(part for part in (prompt, rest) if part is not None)

    def centred(self, text: str) -> str:
        """`text` typeset with its lines as written, each centred on its words (the waits and terminators closing it
        take no room); a line that would cross the window once its names grow is wrapped first, and a piece still too wide
        is set at the left."""
        lines: list[str] = []
        for line in typeset(text).split("\n"):
            words, tags = TRAILING_TAGS.fullmatch(line).groups()  # type: ignore[union-attr]
            words = words.strip(" ")
            if not words:
                lines.append(line)
                continue
            pieces = self.layout.reflow(words).split("\n") if not self.fits_centred(words) else [words]
            lines += [self.centre(CENTRE_MARK + piece) if self.fits_centred(piece) else piece for piece in pieces]
            lines[-1] += tags
        return "\n".join(lines)

    def place(self, line: str) -> str:
        return self.layout.place(line)

    def fits_centred(self, line: str) -> bool:
        """Whether `line`, centred at its default width, stays in the window with its names at their widest."""
        return 2 * self.width(line) <= self.line_width + self.default_width(line)

    def centre(self, line: str) -> str:
        """`line` centred to the pixel whatever its indentation (two spaces or more): spaces, then one FINE_SPACES
        glyph for what's left of the indent."""
        if not line.startswith(CENTRE_MARK):
            return line
        text = line.lstrip(" ")
        spaces, rest = divmod(max(0, self.line_width - self.default_width(text)) // 2, self.space_width)
        return " " * spaces + (f"[{FINE_SPACES + rest - 1:#04x}]" if rest else "") + text

    def overflows(self, text: str) -> Iterator[tuple[str, int]]:
        return self.layout.overflows(text)


def default_layout() -> DialogLayout:
    return DialogLayout(Table(str(TABLE)), dialog_font(), read_names(NAMES))


def stepped(text: str) -> str:
    """`text` typeset with its lines as written, each line of a block a STEP further in than the one before: the
    epilogue's staircase. A blank line starts the next block at the left."""
    lines: list[str] = []
    step = 0
    for line in typeset(text).split("\n"):
        words = line.strip(" ")
        if TERMINATORS.sub("", words):
            lines.append(STEP * step + words)
            step += 1
        else:
            lines.append(line)
            step = 0
    return "\n".join(lines)


def is_choice(text: ET.Element) -> bool:
    """Whether `text` is a choice's prompt: the dump marks it choice="yes_no" or "multiple" from the room script."""
    return text.get("choice") is not None


def alignment(text: ET.Element) -> str:
    """How the build sets `text`'s lines: its align attribute, else CENTER when the script shows it without a window,
    else LEFT."""
    return text.get("align", CENTER if text.get("window") == "none" else LEFT)


def script_overflows(layout: DialogLayout, dialogs: Path = DIALOGS) -> Iterator[Overflow]:
    """Lines still wider than the window once reflowed: kept lines (cards, choices) and words too long to break."""
    for path in sorted(dialogs.glob("*.xml")):
        for text in ET.parse(path).getroot():
            refs = " ".join(ref.text or "" for ref in text.iter("ref"))
            data = text.findtext("data") or ""
            laid_out = layout.reflow(data, choice=is_choice(text), align=alignment(text))
            for line, width in layout.overflows(laid_out):
                yield Overflow(path.stem, refs, line, width)


def main() -> int:
    overflows = list(script_overflows(default_layout()))
    for overflow in overflows:
        print(f"{overflow.room} [{overflow.refs}] {overflow.width}px: {overflow.line}")
    print(f"{len(overflows)} line(s) wider than {LINE_WIDTH} pixels")
    return 1 if overflows else 0


if __name__ == "__main__":
    sys.exit(main())
