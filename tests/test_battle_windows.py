"""
Scenario 00's player phase on the battle map: the command window, and a unit's skill list after moving, are BG1
windows whose strings draw through small_vwf into the window font. So is the START menu, whose strings outgrow
their Japanese character counts but not their cells.
"""


def open_command_window(console):
    console.load("battle-map")
    lines = console.count_calls("panel_put_char_hook")
    console.tap(console.button.A)
    console.run_until(lambda: bool(lines), limit=300)
    console.emu.run_frames(60)


def test_command_window_draws_with_the_small_vwf(console):
    open_command_window(console)
    assert console.matches_golden("battle-commands")


def test_skill_window_draws_with_the_small_vwf(console):
    open_command_window(console)
    for button in (console.button.A, console.button.UP, console.button.A, console.button.A):
        console.tap(button)
        console.emu.run_frames(60)
    assert console.matches_golden("battle-skills")


def test_start_menu_draws_whole_strings_in_the_vanilla_column(console):
    console.load("battle-map")
    lines = console.count_calls("panel_put_char_hook")
    console.tap(console.button.START)
    console.run_until(lambda: bool(lines), limit=300)
    console.emu.run_frames(60)
    assert console.matches_golden("battle-start-menu")


WINDOW_FONT = 0x3000  # VRAM word of the window font's code 0
WINDOW_SLOTS = range(0x333, 0x360)  # BG1 tiles of the window slots: the window font's kana
WINDOW_MAP = 0x4800


def stale_window_cells(console, font: dict[int, bytes]) -> int:
    """Window slot tiles the BG1 map shows while they still hold the font's kana: their pixels came late."""
    vram = bytes(console.emu.vram_read_range(0, 0x10000))
    shown = {(vram[(WINDOW_MAP + cell) * 2] | vram[(WINDOW_MAP + cell) * 2 + 1] << 8) & 0x3FF for cell in range(0x400)}
    return sum(1 for tile in shown if tile in WINDOW_SLOTS and window_tile(vram, tile) == font[tile])


def window_tile(vram: bytes, tile: int) -> bytes:
    word = WINDOW_FONT + (tile - 0x300) * 16
    return vram[word * 2 : word * 2 + 32]


def test_window_slots_go_up_with_their_tilemap(console):
    console.load("battle-map")
    vram = bytes(console.emu.vram_read_range(0, 0x10000))
    font = {tile: window_tile(vram, tile) for tile in WINDOW_SLOTS}
    console.emu.press(0, console.button.A)
    stale = 0
    for frame in range(120):
        if frame == 6:
            console.emu.release(0, console.button.A)
        console.emu.run_frames(1)
        stale += bool(stale_window_cells(console, font))
    assert stale == 0


def test_quick_save_messages_are_french(console):
    console.load("battle-map")
    console.tap(console.button.START)
    console.emu.run_frames(60)
    console.tap(console.button.DOWN)
    console.tap(console.button.A)  # Sauv. rapide: the engine's own question, moved out of bank C0
    console.emu.run_frames(100)
    assert console.matches_golden("battle-save-prompt")
    console.tap(console.button.A)  # Oui
    console.emu.run_frames(100)
    assert console.matches_golden("battle-save-done")


def test_enemy_spell_banner_names_the_spell(console):
    console.load("battle-map")
    for button in (console.button.A, console.button.A, console.button.DOWN, console.button.A, console.button.UP):
        console.tap(button)  # move Byuu's party, then onto Fin
        console.emu.run_frames(80)
    console.tap(console.button.A)  # end the phase: an enemy casts, its spell's name and level in a message
    console.emu.run_frames(160)
    assert console.matches_golden("battle-enemy-spell")


def test_dragon_orders_and_its_full_name(console):
    open_command_window(console)
    for button in (console.button.DOWN, console.button.DOWN, console.button.A):
        console.tap(button)
        console.emu.run_frames(20)
    console.emu.run_frames(40)
    assert console.matches_golden("battle-dragon-orders")  # an 8-letter party name stops at its 8 codes
