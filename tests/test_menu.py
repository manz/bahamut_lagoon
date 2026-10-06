"""
Scenario 01's organisation screen, from the debug jump: names and classes past their records draw through small_vwf,
on BG3 (the unit's dragon) and BG2 (the party).
"""


def test_organisation_names_draw_with_the_small_vwf(console):
    console.load("menu-organisation")
    names = console.count_calls("menu_draw_fixed_name")
    console.tap(console.button.B)
    console.run_until(lambda: bool(names), limit=1200)
    console.emu.run_frames(90)
    assert console.matches_golden("menu-organisation")
