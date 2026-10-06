"""
Dragon feed menu (savestate on the Nourrir / Sortir choice): the item list opens, and the selected item's
description is drawn with the VWF (src/description_vwf.s) from the relocated messages (src/item_descriptions.s).

Before those two, the list read the descriptions in the wrong bank and stalled on a data byte that reads as
"wait for a key".
"""


def test_feed_menu_describes_the_selected_item(console):
    glyphs = console.count_calls("description_char")
    console.load("feed-menu")
    console.tap(console.button.A)  # Nourrir: the item list
    console.emu.run_frames(90)
    console.tap(console.button.DOWN)
    console.tap(console.button.DOWN)  # Burning Axe: "Hache de Feu"
    console.run_until(lambda: len(glyphs) >= len("Hache de Feu"), limit=120)
    console.emu.run_frames(60)
    assert not console.emu.get_state().stp
    assert console.matches_golden("feed-menu")
