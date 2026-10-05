"""
Load game screen from the title, with three chapter saves on the cart.

Only checks that the screen opens through the pooled load game VWF: the chapter name blit is unfinished, so what
it draws is not asserted yet.
"""


def test_load_screen_draws_slots_with_the_pooled_vwf(console):
    calls = console.count_calls("load_game.vwf_entry_point")
    console.load("title-with-saves")  # cursor on Charger Partie
    console.press_until(console.button.A, lambda: bool(calls))
    console.emu.run_frames(60)
    assert not console.emu.get_state().stp
