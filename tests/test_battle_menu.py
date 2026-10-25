"""
The menu before a battle, mid-game (savestate on Sortie): the Dragon screen and the Infos descriptions page used to
freeze. The Dragon screen typed message 0x275 at once, four DMA queue entries a glyph, until the queue ran over the
sound driver's variables at 1D00 and the next sound waited forever; the descriptions page drew enough names that the
BG3 run collection started over endlessly.
"""

from kintsuki import CallbackKind

from tests.conftest import Console


def open_menu_entry(console: Console, ups: int) -> None:
    console.load("before-battle-menu")
    for _ in range(ups):
        console.tap(console.button.UP)
    console.tap(console.button.A)
    console.emu.run_frames(240)


def cursor_moves(console: Console, button: int) -> bool:
    before = bytes(console.emu.oam_read_range())
    console.tap(button)
    console.emu.run_frames(60)
    return bytes(console.emu.oam_read_range()) != before


def test_dragon_screen_answers(console: Console) -> None:
    open_menu_entry(console, 4)  # Dragon
    assert cursor_moves(console, console.button.RIGHT)
    assert console.matches_golden("battle-menu-dragons")


def test_infos_descriptions_answer(console: Console) -> None:
    open_menu_entry(console, 3)  # Infos
    console.tap(console.button.DOWN)
    console.tap(console.button.A)  # Descriptions
    console.emu.run_frames(150)
    assert cursor_moves(console, console.button.DOWN)
    assert console.matches_golden("battle-menu-descriptions")


def test_map_titles_the_chapter(console: Console) -> None:
    open_menu_entry(console, 1)  # Carte
    assert console.matches_golden("battle-menu-map")


def test_map_unit_info_draws_with_the_small_vwf(console: Console) -> None:
    open_menu_entry(console, 1)  # Carte
    console.tap(console.button.A)  # past the chapter title
    console.emu.run_frames(90)
    for button in (console.button.UP,) * 4 + (console.button.LEFT,):
        console.tap(button)  # onto the enemy at the top left
    console.tap(console.button.A)  # its box: C0A9B8, copied and drawn through the battle panel's VWF
    console.emu.run_frames(120)
    assert console.matches_golden("battle-menu-unit-info")


def test_dragon_team_names_keep_their_neighbours(console: Console) -> None:
    open_menu_entry(console, 4)  # Dragon
    console.tap(console.button.A)
    console.emu.run_frames(150)
    console.tap(console.button.DOWN)  # team 4: Matelite's field reaches the column Défense starts in
    console.emu.run_frames(60)
    assert console.matches_golden("battle-menu-dragon-team")


UNIT_NAME_READ = 0xC0DD5A  # LDA 7E0011,X: the unit's enemy kind, which indexes its name record
MORTWASSER = 0x84
OEIL_DE_BOEUF = 0x9B


def test_unit_info_draws_the_oe_ligature(console: Console) -> None:
    """Œil-de-bœuf, in the box test_map_unit_info_draws_with_the_small_vwf opens: no savestate meets one, so its
    Mortwassers take that kind as the box reads it."""

    def swap(pc: int, value: int) -> None:
        kind = 0x7E0011 + console.emu.get_state().x
        if console.emu.read(kind) == MORTWASSER:
            console.emu.write(kind, OEIL_DE_BOEUF)

    open_menu_entry(console, 1)  # Carte
    console.tap(console.button.A)
    console.emu.run_frames(90)
    for button in (console.button.UP,) * 4 + (console.button.LEFT,):
        console.tap(button)
    callback = console.emu.add_exec_callback(UNIT_NAME_READ, UNIT_NAME_READ, swap)
    console.tap(console.button.A)
    console.emu.run_frames(120)
    console.emu.remove_callback(CallbackKind.EXEC, callback)
    assert console.matches_golden("battle-menu-unit-info-oe")
