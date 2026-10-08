"""
Dialog text against the window it is drawn in, measured with katsuji in the dialogue font.

The field engine's window (`DA36AE`) is 32 tiles wide: a corner, 30 tiles, a corner. Text starts at column 1, so a
line holds 240 pixels. Lines go to a 256-pixel buffer and wrap nowhere: a longer line runs under the frame. Pages
turn by themselves once a window's lines are full (`DA3E1A`), so only the width matters: the build reflows each
paragraph to it.

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
GLUED = re.compile(r"[?!;:»]")  # French puts a space before these: it must not break the line
RIGHT_OF_CENTRE = 10  # pixels: an indented line set further right than this is right-aligned (a signature)
COMMA = re.compile(r",(?=[^\s\d\]])|(?<=\D),(?=\d)")  # a comma touching the next word (not 1,5)
ELLIPSIS = re.compile(r"(\.\.\.+)(?![\s.?!,;:\]»]|\[end|$)")  # an ellipsis touching the next word
NAME_CODE = re.compile(r"\[character\]\[0x[0-9a-fA-F]+\]$")
GLYPH_CODE = re.compile(r"\[0x[0-9a-fA-F]+\]$")
SPEAKER = re.compile(r"(\[character\]\[0x[0-9a-fA-F]+\]|[^\s:.?!,]+(?: [^\s:.?!,]+){0,2}):")  # "Roi de Kana:"
SPACES = re.compile(r"(?<=\S)  +(?=\S)")
LIST_ITEM = re.compile(r"(\d+|\[0x(af|b[0-8])\])+ ?[-.)]")  # "1- ", "[0xb0]- ": an item, a line of its own
BLOCK = "\x00"  # between the line groups _wrap_line returns: a group never splits over two windows
SENTENCE_END = re.compile(r"[.!?…](\[end1?\])?$")


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
        self.default_names = list(self.names)
        widest = max(NAME_LETTERS, key=lambda letter: self.wrapper.measure(table.to_bytes(letter)))
        self.names[:RENAMEABLE] = [table.to_bytes(widest * NAME_CODES)] * RENAMEABLE
        self.line_width = line_width

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

    def reflow(self, text: str, page_lines: int | None = None, keep_lines: bool = False) -> str:
        """`text` set in French typography (`typeset`), then laid out to the window: each paragraph's lines joined
        and wrapped again by sentences.

        Kept as written: blank lines, spaces only or not (they separate paragraphs), a speaker label or a -heading-
        alone on its line, lines starting with one space (choices) or two and more (placed: `place`), and texts
        ending in [end1] (a choice follows them) or given `keep_lines` (a choice's prompt, its options a line each).
        A numbered line (1- or [0xb0]-) is a paragraph of its own. Given the window's `page_lines`, a block of lines
        that would run past the window's last line starts the next window instead (`paginate`)."""
        if keep_lines or text.endswith("[end1]"):
            return "\n".join(typeset(line) for line in text.split("\n"))
        lines = [typeset(line) for line in text.split("\n")]
        indented = [line for line in lines if line.startswith("  ") and line.strip()]
        block_indent = len(indented) > 1 and len({len(line) - len(line.lstrip(" ")) for line in indented}) == 1
        blocks: list[list[str]] = []
        paragraph: list[str] = []

        def close_paragraph() -> None:
            if paragraph:
                blocks.extend(line.split("\n") for line in self._wrap_line(" ".join(paragraph)).split(BLOCK))
                paragraph.clear()

        for line in lines:
            if not line.strip():
                close_paragraph()
                blocks.append([""])  # a spacer, spaces or not, draws nothing
            elif line.startswith(" ") or SPEAKER_LABEL.fullmatch(line) or HEADING.fullmatch(line):
                close_paragraph()
                blocks.append([line if block_indent else self.place(line)])
            elif LIST_ITEM.match(line):
                close_paragraph()
                paragraph.append(line)
                close_paragraph()
            else:
                paragraph.append(line)
        close_paragraph()
        if page_lines is not None:
            blocks = paginate(blocks, page_lines)
        return "\n".join(line for block in blocks for line in block)

    def place(self, line: str) -> str:
        """A line starting with two spaces or more, re-indented in the window: right-aligned when it was set well
        right of the middle (a signature, -SENDACK-), else centred; within half a space, the indent's unit. Lines
        starting with one space (choices) or none stay as they are."""
        if not line.startswith("  "):
            return line
        text = line.lstrip(" ")
        space = self.wrapper.measure(bytes([SPACE]))
        width = self.default_width(text)
        was_right_of_centre = (len(line) - len(text)) * space + width / 2 - self.line_width / 2 > RIGHT_OF_CENTRE
        margin = self.line_width - width if was_right_of_centre else (self.line_width - width) // 2
        return " " * (max(0, margin) // space if was_right_of_centre else round(max(0, margin) / space)) + text

    def centre(self, line: str) -> str:
        """`line` centred whatever its indentation (two spaces or more)."""
        if not line.startswith("  "):
            return line
        return self.place("  " + line.lstrip(" "))

    def default_width(self, line: str) -> int:
        """`line`'s width with every name at its default spelling: where it sits, not how wide it may grow."""
        return self.wrapper.measure(self.encode(line, self.default_names))

    def _wrap_line(self, line: str) -> str:
        """`line` laid out by sentences: sentences share a line while they fit, a sentence that does not fit after
        the line so far starts its own, and one wider than the window breaks at spaces, katsuji's way (a word that
        would pass the width starts a new line), its last line taking no further sentence."""
        lines: list[str] = []
        current = ""
        for sentence in self._sentences(line):
            candidate = f"{current} {sentence}" if current else sentence
            if self.width(candidate) <= self.line_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            if self.width(sentence) <= self.line_width:
                current = sentence
            else:
                lines.append("\n".join(self._break_words(sentence)))
                current = ""
        if current:
            lines.append(current)
        return BLOCK.join(lines)

    @staticmethod
    def _words(text: str) -> list[str]:
        """Words, with a French ? ! ; : » kept on the word before it."""
        words: list[str] = []
        for word in text.split(" "):
            if words and GLUED.match(word):
                words[-1] += f" {word}"
            else:
                words.append(word)
        return words

    def _sentences(self, text: str) -> list[str]:
        """`text` cut after each word ending a sentence (. ! ? or …, before a terminator)."""
        sentences: list[str] = []
        current: list[str] = []
        for word in self._words(text):
            current.append(word)
            if SENTENCE_END.search(word):
                sentences.append(" ".join(current))
                current = []
        if current:
            sentences.append(" ".join(current))
        return sentences

    def _break_words(self, sentence: str) -> list[str]:
        """`sentence` broken at spaces into as few lines as the window allows, balanced: the narrowest width that
        still needs no more lines, so the last line is not left with a word or two."""
        lines = self._greedy(sentence, self.line_width)
        narrow, wide = 1, self.line_width
        while narrow < wide:
            middle = (narrow + wide) // 2
            if len(self._greedy(sentence, middle)) <= len(lines):
                wide = middle
            else:
                narrow = middle + 1
        return self._greedy(sentence, wide)

    def _greedy(self, sentence: str, width: int) -> list[str]:
        """Words fill each line up to `width`; a word that would pass it starts the next."""
        lines: list[str] = []
        current = ""
        for word in self._words(sentence):
            candidate = f"{current} {word}" if current else word
            if current and self.width(candidate) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
        return lines

    def overflows(self, text: str) -> Iterator[tuple[str, int]]:
        """The lines of `text` wider than the window, with their width."""
        for line in text.split("\n"):
            width = self.width(line)
            if width > self.line_width:
                yield line, width


def typeset(line: str) -> str:
    """`line` in French typography: a space after a comma and after an ellipsis that runs into a word, a space
    before ? ! ; and before : (not after a speaker's name opening the line), single spaces between words. A glyph
    code ([0xd8]) keeps what follows it tight, a name ([character][0x0]) does not. The indentation is left alone."""
    indent = line[: len(line) - len(line.lstrip(" "))]
    text = line[len(indent) :]
    text = COMMA.sub(", ", text)
    text = ELLIPSIS.sub(r"\1 ", text)
    text = _space_before(text, "?!;")
    speaker = SPEAKER.match(text)
    head, rest = (text[: speaker.end()], text[speaker.end() :]) if speaker else ("", text)
    text = head + _space_before(rest, ":")
    return indent + SPACES.sub(" ", text)


def _space_before(text: str, marks: str) -> str:
    """A space before each run of `marks` that touches the word before it; after a glyph code, none."""
    out = []
    for index, char in enumerate(text):
        if char in marks and index and text[index - 1] not in " " + marks:
            before = text[:index]
            if before.endswith("]") and GLYPH_CODE.search(before) and not NAME_CODE.search(before):
                out.append(char)
                continue
            out.append(" ")
        out.append(char)
    return "".join(out)


def paginate(blocks: list[list[str]], page_lines: int) -> list[list[str]]:
    """`blocks` (groups of lines) laid over windows of `page_lines` lines. The engine turns the window once it is
    full (`DA3E1A`, the player presses A), so a group that would cross into the next window is pushed there by
    blank lines; a speaker label stays with the group after it; a blank line that would open a window is dropped."""
    out: list[list[str]] = []
    row = 0
    pending_label: list[str] = []
    for block in blocks:
        if block == [""] and not pending_label:
            if row % page_lines == 0 and out:
                continue
            out.append(block)
            row += 1
            continue
        if len(block) == 1 and SPEAKER_LABEL.fullmatch(block[0]) and not pending_label:
            pending_label = block
            continue
        lines = pending_label + block
        pending_label = []
        used = row % page_lines
        if used and used + len(lines) > page_lines and len(lines) <= page_lines:
            out.append([""] * (page_lines - used))
            row += page_lines - used
        out.append(lines)
        row += len(lines)
    if pending_label:
        out.append(pending_label)
    return out


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
