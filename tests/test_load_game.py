"""
Load game screen from the title, with three chapter saves on the cart: the chapter titles and the prompt are
drawn by the VWF into the 4bpp text buffer (src/text_buffer_vwf.s).
"""

from tests.conftest import Console


def test_load_screen_draws_titles_and_prompt(console: Console) -> None:
    titles = console.count_calls("draw_string")
    prompts = console.count_calls("draw_message")
    console.load("title-with-saves")  # cursor on Charger Partie
    console.press_until(console.button.A, lambda: len(titles) == 3 and bool(prompts))
    console.emu.run_frames(60)
    assert not console.emu.get_state().stp
    assert console.matches_golden("load-screen")
