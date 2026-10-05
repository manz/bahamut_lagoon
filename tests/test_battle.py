"""
Scenario 00's battle, reached from the debug menu: jump to scenario 00, skip its opening event, and the battle
opens with Matelite's lines in the battle message window.
"""


def test_battle_text_draws_with_the_pooled_vwf(console):
    console.load("debug-scenario-jump")
    console.press_until(console.button.DOWN, lambda: console.shows("JUMP TO SCENARIO  00"))
    console.press_until(console.button.A, lambda: console.shows("SKIP EVENT"))
    calls = console.count_calls("battle_vwf_char")
    console.tap(console.button.B)  # skip the event, straight to the battle map
    console.run_until(lambda: bool(calls), limit=1800)
    console.emu.run_frames(60)
    assert not console.emu.get_state().stp
