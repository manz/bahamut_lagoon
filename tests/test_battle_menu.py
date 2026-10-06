"""
The menu before a battle, mid-game (savestate on Sortie): the Infos descriptions page used to freeze, drawing
enough names that the BG3 run collection started over endlessly.
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


def test_infos_descriptions_answer(console):
    open_menu_entry(console, 3)  # Infos
    console.tap(console.button.DOWN)
    console.tap(console.button.A)  # Descriptions
    console.emu.run_frames(150)
    assert cursor_moves(console, console.button.DOWN)
    assert console.matches_golden("battle-menu-descriptions")
