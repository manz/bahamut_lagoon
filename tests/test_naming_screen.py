"""
The naming screen, opened from scenario 00's opening: Byuu's name above its page labels (tiles of their own), and
three pages of French characters drawn in the menu font. The tests continue from each other, in file order.
"""

from pathlib import Path

from katsuji.formats import VwfFont

NAMING_CURSOR = 0xEE468E  # update_naming_cursor_pos: runs while the screen takes input
NAME = 0x7E9E00  # the name being edited, FF-terminated
CURSOR_X = 0x0010D6  # the name cursor object's x
NAME_X = 0x3A  # its x before the first character
PAGE_CURSOR_X = 0x001056  # the page cursor object's x
LABEL_STOPS = [52, 116, 180, 220]  # 4 pixels before Majuscules, Minuscules, Autre, Fin


def test_the_name_and_the_page_labels_do_not_overlap(console):
    console.load("before-naming")
    opened = []
    console.emu.add_exec_callback(NAMING_CURSOR, NAMING_CURSOR, lambda pc, value: opened.append(pc))
    console.press_until(console.button.A, lambda: bool(opened), limit=10)
    console.emu.run_frames(60)
    assert console.matches_golden("naming-capitals")


def test_the_page_cursor_stops_before_each_label(console):
    stops = []
    for _ in LABEL_STOPS:
        stops.append(console.emu.read16(PAGE_CURSOR_X))
        console.tap(console.button.RIGHT)
    assert stops == LABEL_STOPS


def test_the_lower_case_page(console):
    console.tap(console.button.RIGHT)
    console.tap(console.button.A)
    console.emu.run_frames(30)
    assert console.matches_golden("naming-lower-case")


def test_the_punctuation_page(console):
    console.tap(console.button.RIGHT)
    console.tap(console.button.A)
    console.emu.run_frames(30)
    assert console.matches_golden("naming-punctuation")


def test_a_letter_types_its_code(console):
    for button in (console.button.LEFT, console.button.LEFT, console.button.A, console.button.DOWN, console.button.A):
        console.tap(button)
    console.emu.run_frames(20)
    name = bytes(console.emu.read_range(NAME, 8))
    assert name[: name.index(0xFF)].endswith(bytes([0xB9]))  # A


def test_the_name_cursor_follows_the_name_s_width(console):
    font = VwfFont.decode(Path("assets/vwf.bin").read_bytes())
    name = bytes(console.emu.read_range(NAME, 8))
    width = sum(font.widths[code] + 1 for code in name[: name.index(0xFF)])
    assert console.emu.read16(CURSOR_X) == NAME_X + width
