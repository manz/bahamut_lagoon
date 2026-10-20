"""
A field dialog right after New Game: Kana's lagoon once the intro hands the player Byuu (new-game-field), Rush
spoken to. The dialogue VWF draws the French line, typeset and wrapped at build time.
"""

from tests.conftest import Console


def test_rush_s_first_line(console: Console) -> None:
    console.load("new-game-field")
    for button in (console.button.LEFT, console.button.UP):
        console.emu.press(0, button)
        console.emu.run_frames(40)
        console.emu.release(0, button)
        console.tap(console.button.A)
        console.emu.run_frames(60)
    console.emu.run_frames(120)  # the typewriter done
    assert console.matches_golden("field-dialog-rush")
