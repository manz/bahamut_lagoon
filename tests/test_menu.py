"""
Scenario 01's organisation screen, from the debug jump: names and classes past their records draw through small_vwf,
on BG3 (the unit's dragon) and BG2 (the party). The equip screens add draw_menu_string's labels and placeholders and
inline labels laid out in fields wider than their text.
"""


def test_organisation_names_draw_with_the_small_vwf(console):
    console.load("menu-organisation")
    names = console.count_calls("menu_draw_fixed_name")
    console.tap(console.button.B)
    console.run_until(lambda: bool(names), limit=1200)
    console.emu.run_frames(90)
    assert console.matches_golden("menu-organisation")


def test_equip_labels_draw_with_the_small_vwf(console):
    console.load("menu-organisation")
    names = console.count_calls("menu_draw_fixed_name")
    console.tap(console.button.B)
    console.run_until(lambda: bool(names), limit=1200)
    console.emu.run_frames(90)
    console.tap(console.button.UP)
    console.tap(console.button.UP)  # Equiper
    console.tap(console.button.A)  # the party list: NV labels
    console.emu.run_frames(120)
    assert console.matches_golden("menu-party")
    console.tap(console.button.A)  # Byuu: Atk. to Mag. in 8-cell fields, --- placeholders
    console.emu.run_frames(120)
    assert console.matches_golden("menu-equip")
