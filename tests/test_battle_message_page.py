"""
A battle message's next page, scenario 00's opening: Matelite's two lines, the window paused. The engine's pause
scrolls its text buffer up a line; the VWF starts the page at the top, so it blanks the three lines first, or the old
second line shows in the first until the pen writes over each column (src/battle_vwf_reloc.s).
"""

from tests.conftest import Console

TEXT_VRAM = 0x4180 * 2  # the battle text's first 8x16 column, a byte address
COLUMN_BYTES = 0x20
COLUMNS = 0x1E  # a line
PEN_COLUMNS = 8  # the new page's first columns, which the pen may have reached
PRESS = 4  # frames A is held
TYPING = 8  # frames after it: the page turned, the pen a few columns in


def test_next_page_starts_blank(console: Console) -> None:
    console.load("battle-message-page")
    emu = console.emu
    emu.press(0, console.button.A)
    emu.run_frames(PRESS)
    emu.release(0, console.button.A)
    emu.run_frames(TYPING)
    vram = bytes(emu.vram_read_range(TEXT_VRAM, COLUMNS * 2 * COLUMN_BYTES))
    inked = [c for c in range(PEN_COLUMNS, COLUMNS * 2) if any(vram[c * COLUMN_BYTES : (c + 1) * COLUMN_BYTES])]
    assert inked == []
