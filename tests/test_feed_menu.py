"""
Dragon feed menu (savestate on the Nourrir / Sortir choice): the item list opens, and the selected item's
description is drawn with the VWF (src/description_vwf.s) from the relocated messages (src/item_descriptions.s).
The names survive the font the screen loads again when it reopens from the field.

Before those two, the list read the descriptions in the wrong bank and stalled on a data byte that reads as
"wait for a key".
"""


def test_feed_menu_describes_the_selected_item(console):
    glyphs = console.count_calls("description_char")
    console.load("feed-menu")
    console.tap(console.button.B)
    console.emu.run_frames(60)
    console.tap(console.button.B)  # out of the menu: the savestate's header was drawn before the patch
    console.emu.run_frames(90)
    console.tap(console.button.A)  # back in: the header redrawn
    console.emu.run_frames(90)
    console.tap(console.button.A)  # Nourrir: the item list
    console.emu.run_frames(90)
    console.tap(console.button.DOWN)
    console.tap(console.button.DOWN)  # Burning Axe: "Hache de Feu"
    console.run_until(lambda: len(glyphs) >= len("Hache de Feu"), limit=120)
    console.emu.run_frames(60)
    assert not console.emu.get_state().stp
    assert console.matches_golden("feed-menu")


def test_feed_menu_redraws_its_names_after_the_field(console):
    console.load("feed-menu")
    console.tap(console.button.B)
    console.emu.run_frames(60)
    console.tap(console.button.B)
    console.emu.run_frames(120)
    console.tap(console.button.DOWN)
    console.tap(console.button.A)  # Sortir: back to the field
    console.emu.run_frames(200)
    for _ in range(6):
        console.tap(console.button.B)
        console.emu.run_frames(100)
    console.tap(console.button.A)  # the dragon again: the screen loads its font over the name slots
    console.emu.run_frames(150)
    assert console.matches_golden("feed-menu-reentry")
