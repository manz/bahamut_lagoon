"""
The menu before a battle, mid-game (savestate on Sortie): the Dragon screen and the Infos descriptions page used to
freeze. The Dragon screen typed message 0x275 at once, four DMA queue entries a glyph, until the queue ran over the
sound driver's variables at 1D00 and the next sound waited forever; the descriptions page drew enough names that the
BG3 run collection started over endlessly.
"""


def open_menu_entry(console, ups: int) -> None:
    console.load("before-battle-menu")
    for _ in range(ups):
        console.tap(console.button.UP)
    console.tap(console.button.A)
    console.emu.run_frames(240)


def cursor_moves(console, button: int) -> bool:
    before = bytes(console.emu.oam_read_range())
    console.tap(button)
    console.emu.run_frames(60)
    return bytes(console.emu.oam_read_range()) != before


def test_dragon_screen_answers(console):
    open_menu_entry(console, 4)  # Dragon
    assert cursor_moves(console, console.button.RIGHT)
    assert console.matches_golden("battle-menu-dragons")


def test_infos_descriptions_answer(console):
    open_menu_entry(console, 3)  # Infos
    console.tap(console.button.DOWN)
    console.tap(console.button.A)  # Descriptions
    console.emu.run_frames(150)
    assert cursor_moves(console, console.button.DOWN)
    assert console.matches_golden("battle-menu-descriptions")


def test_map_titles_the_chapter(console):
    open_menu_entry(console, 1)  # Carte
    assert console.matches_golden("battle-menu-map")


def test_map_unit_info_draws_with_the_small_vwf(console):
    open_menu_entry(console, 1)  # Carte
    console.tap(console.button.A)  # past the chapter title
    console.emu.run_frames(90)
    for button in (console.button.UP,) * 4 + (console.button.LEFT,):
        console.tap(button)  # onto the enemy at the top left
    console.tap(console.button.A)  # its box: C0A9B8, copied and drawn through the battle panel's VWF
    console.emu.run_frames(120)
    assert console.matches_golden("battle-menu-unit-info")
