"""
Scenario 00's player phase on the battle map: the command window, and a unit's skill list after moving, are BG1
windows whose strings draw through small_vwf into the window font. So is the START menu, whose strings outgrow
their Japanese character counts but not their cells.
"""


def open_command_window(console):
    console.load("battle-map")
    lines = console.count_calls("panel_put_char_hook")
    console.tap(console.button.A)
    console.run_until(lambda: bool(lines), limit=300)
    console.emu.run_frames(60)


def test_command_window_draws_with_the_small_vwf(console):
    open_command_window(console)
    assert console.matches_golden("battle-commands")


def test_skill_window_draws_with_the_small_vwf(console):
    open_command_window(console)
    for button in (console.button.A, console.button.UP, console.button.A, console.button.A):
        console.tap(button)
        console.emu.run_frames(60)
    assert console.matches_golden("battle-skills")


def test_start_menu_draws_whole_strings_in_the_vanilla_column(console):
    console.load("battle-map")
    lines = console.count_calls("panel_put_char_hook")
    console.tap(console.button.START)
    console.run_until(lambda: bool(lines), limit=300)
    console.emu.run_frames(60)
    assert console.matches_golden("battle-start-menu")
