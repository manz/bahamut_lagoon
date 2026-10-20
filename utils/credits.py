"""
The staff credits in their own charset, text/table/intro.tbl: small capitals from 0x01, capitals from 0x1D, no accent
nor punctuation, drawn with the 8x16 font at E8:CD55.

The attract mode's (room 250): text/fr/dialog/0250.xml holds each credit as plain lines. The room spells them out
centred in 30 columns (the odd column goes to the left margin) with 0xF0, the typewriter's step, around every character.

The ending's (room 248): op 85 draw_credit_line(x, y, text) (DA6D88, DA7571) writes one FF-terminated line into the BG
tilemap buffer at 7E6000 + y * 64 + x * 2, code c as tile ((c & 0x70) << 1 | c & 0x0F) + 8: a small capital takes one
tile, a capital (0x1D on) two, the bottom half 0x10 tiles on, one row down. text/fr/dialog/0248.xml holds a line per
string; a string whose French moves it carries its column in an `x` attribute, written over the opcode's x operand.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from utils.vm.room import Room, element_text

CREDITS_ROOMS = frozenset({250})
ENDING_CREDITS_ROOMS = frozenset({248})
SCREEN_COLUMNS = 32  # the ending's tilemap: a line runs from its x to the screen's right edge
TABLE = Path("text/table/intro.tbl")
COLUMNS = 30  # the credits' text area: vanilla centres its lines there, by hand
STEP = "[0xf0]"
CHARACTER = re.compile(r"\[0x[0-9a-f]+\]|.")  # a code the table has no letter for ([0x37]) is one character
TERMINATOR = re.compile(r"(\[end1?\])+$")
LAST_CREDIT = "[end][end]"  # the room's last string: its last character goes without a step


def credits_script(text: str) -> str:
    """`text`'s lines centred and stepped as the room spells them, its terminator kept."""
    terminator = TERMINATOR.search(text)
    end = terminator.group(0) if terminator else ""
    lines = text[: len(text) - len(end)].split("\n")
    spelled = "\n".join(_spell(line) for line in lines)
    if end == LAST_CREDIT:
        spelled = spelled.removesuffix(STEP)
    return spelled + end


def _spell(line: str) -> str:
    characters = CHARACTER.findall(line)
    if len(characters) > COLUMNS:
        raise ValueError(f"credit line wider than {COLUMNS} columns: {line!r}")
    margin = [" "] * ((COLUMNS - len(characters) + 1) // 2)
    return "".join(STEP + character for character in margin + characters) + STEP


def place_credit_lines(room: Room, texts: ET.Element) -> None:
    """Move each ending credit carrying an `x` to that column (the x operand sits two bytes before the text pointer);
    refuse a line, moved or not, that runs past the screen's right edge."""
    for text in texts:
        line = TERMINATOR.sub("", text.findtext("data", ""))
        column = text.get("x")
        for ref in text.iter("ref"):
            operand = int(element_text(ref), 16) - 2
            if column is not None:
                room.room[operand] = int(column, 0)
            if room.room[operand] + len(CHARACTER.findall(line)) > SCREEN_COLUMNS:
                raise ValueError(
                    f"ending credit runs past column {SCREEN_COLUMNS} from x {room.room[operand]}: {line!r}"
                )
