"""
Load game screen from the title, with three chapter saves on the cart: the chapter titles and the prompt are
drawn by the VWF into the 4bpp text buffer (src/text_buffer_vwf.s).
"""


def test_load_screen_draws_titles_and_prompt(console):
    calls = console.count_calls("draw_string")
    console.load("title-with-saves")  # cursor on Charger Partie
    console.press_until(console.button.A, lambda: len(calls) >= 4)  # three chapter titles, then the prompt
    console.emu.run_frames(60)
    assert not console.emu.get_state().stp
    assert console.matches_golden("load-screen")
