"""
Debug mode, in English: the scenario jump, then the start-event menu, then scenario 00's opening event.

The tests continue from each other on the shared console, in file order.
"""


def test_scenario_jump_is_in_english(console):
    console.load("debug-scenario-jump")  # blank cart: New Game straight from the title
    assert console.shows("JUMP TO SCENARIO")
    console.press_until(console.button.DOWN, lambda: console.shows("JUMP TO SCENARIO  00"))


def test_scenario_jump_opens_the_start_event_menu_in_english(console):
    console.press_until(console.button.A, lambda: console.shows("START EVENT"))
    assert console.shows("START EVENT 00")
    screen = console.screen()
    for line in ("WATCH EVENT  A", "SKIP EVENT   B", "MAP ONLY     Y"):
        assert any(line in row for row in screen), line


def test_opening_event_draws_dialog_with_the_pooled_vwf(console):
    calls = console.count_calls("vwf_char")
    console.tap(console.button.A)
    for _ in range(80):
        console.emu.run_frames(40)
        console.tap(console.button.A)  # advance the dialog
        if calls:
            break
    assert calls, "dialog VWF (vwf_char in the ed_reloc pool) never ran"
    assert not console.emu.get_state().stp
