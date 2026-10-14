"""
The battle squad menu, scenario 1B's first turn, the cursor on Infos. In the original game each visit to Infos leaves
3 bytes on the menu task's stack (block 0E80): about twelve visits and the game hangs (src/squad_menu.s).
"""

from tests.conftest import Console

SQUAD_MENU_S = 0x000EAB  # the menu task's saved stack pointer
VISITS = 20


def test_infos_visits_keep_the_squad_menu_stack(console: Console) -> None:
    console.load("battle-squad-menu")
    emu = console.emu
    saved = emu.read16(SQUAD_MENU_S)
    for _ in range(VISITS):
        console.tap(console.button.A)  # Infos
        emu.run_frames(100)
        console.tap(console.button.B)  # back to the squad menu
        emu.run_frames(100)
    assert not emu.get_state().stp
    assert emu.get_state().pc >> 16 >= 0xC0, "the CPU runs from RAM: the menu task returned into nothing"
    assert emu.read16(SQUAD_MENU_S) == saved
