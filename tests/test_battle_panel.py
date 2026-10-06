"""
Scenario 00's unit panel, from the last line of the opening dialogue: the names draw through small_vwf into the
panel's six cells.
"""


def test_panel_names_draw_with_the_small_vwf(console):
    console.load("battle-panel")
    names = console.count_calls("panel_put_char_hook")
    console.tap(console.button.A)
    console.run_until(lambda: bool(names), limit=300)
    console.emu.run_frames(60)
    assert console.matches_golden("battle-panel")
