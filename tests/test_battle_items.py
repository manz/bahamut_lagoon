"""
Scenario 00's battle, Equipe then Objets: the item list the menu engine draws over the battle, item names past their
eight cells through small_vwf.
"""


def test_battle_item_list_draws_with_the_small_vwf(console):
    console.load("battle-items")
    names = console.count_calls("menu_draw_fixed_name")
    console.tap(console.button.A)
    console.run_until(lambda: bool(names), limit=600)
    console.emu.run_frames(60)
    assert console.matches_golden("battle-items")
