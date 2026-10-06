"""
Scenario 00's unit panel, from the last line of the opening dialogue: names and classes draw through small_vwf,
full names past their eight-code records ("Anastasia", "Ekaterina").
"""


def test_panel_text_draws_with_the_small_vwf(console):
    console.load("battle-panel")
    names = console.count_calls("panel_put_char_hook")
    console.tap(console.button.A)
    console.run_until(lambda: bool(names), limit=300)
    console.emu.run_frames(60)
    assert console.matches_golden("battle-panel")
