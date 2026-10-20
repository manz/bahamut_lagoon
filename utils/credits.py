"""
The attract mode's staff credits (room 250) in their own charset, text/table/intro.tbl: small capitals from 0x01,
capitals from 0x1D, no accent nor punctuation, drawn with the 8x16 font at E8:CD55.

text/fr/dialog/0250.xml holds each credit as plain lines. The room spells them out centred in 30 columns (the odd column
goes to the left margin) with 0xF0, the typewriter's step, around every character.
"""

import re
from pathlib import Path

CREDITS_ROOMS = frozenset({250})
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
