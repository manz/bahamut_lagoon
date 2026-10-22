"""
Scenario 00's player phase on the battle map: the command window, and a unit's skill list after moving, are BG1
windows whose strings draw through small_vwf into the window font. So is the START menu, whose strings outgrow
their Japanese character counts but not their cells. A later map's START menu checks its tilemap's DMA timing.
"""

from kintsuki import CallbackKind

from tests.conftest import Console, symbol


def open_command_window(console: Console) -> None:
    console.load("battle-map")
    lines = console.count_calls("panel_put_char_hook")
    console.tap(console.button.A)
    console.run_until(lambda: bool(lines), limit=300)
    console.emu.run_frames(60)


def test_command_window_draws_with_the_small_vwf(console: Console) -> None:
    open_command_window(console)
    assert console.matches_golden("battle-commands")


def test_skill_window_draws_with_the_small_vwf(console: Console) -> None:
    open_command_window(console)
    for button in (console.button.A, console.button.UP, console.button.A, console.button.A):
        console.tap(button)
        console.emu.run_frames(60)
    assert console.matches_golden("battle-skills")


def test_start_menu_draws_whole_strings_in_the_vanilla_column(console: Console) -> None:
    console.load("battle-map")
    lines = console.count_calls("panel_put_char_hook")
    console.tap(console.button.START)
    console.run_until(lambda: bool(lines), limit=300)
    console.emu.run_frames(60)
    assert console.matches_golden("battle-start-menu")


WINDOW_FONT = 0x3000  # VRAM word of the window font's code 0
WINDOW_SLOTS = range(0x333, 0x360)  # BG1 tiles of the window slots: the window font's kana
WINDOW_MAP = 0x4800


def stale_window_cells(console: Console, font: dict[int, bytes]) -> int:
    """Window slot tiles the BG1 map shows while they still hold the font's kana: their pixels came late."""
    vram = bytes(console.emu.vram_read_range(0, 0x10000))
    shown = {(vram[(WINDOW_MAP + cell) * 2] | vram[(WINDOW_MAP + cell) * 2 + 1] << 8) & 0x3FF for cell in range(0x400)}
    return sum(1 for tile in shown if tile in WINDOW_SLOTS and window_tile(vram, tile) == font[tile])


def window_tile(vram: bytes, tile: int) -> bytes:
    word = WINDOW_FONT + (tile - 0x300) * 16
    return vram[word * 2 : word * 2 + 32]


def test_window_slots_go_up_with_their_tilemap(console: Console) -> None:
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


def test_quick_save_messages_are_french(console: Console) -> None:
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


def test_enemy_spell_banner_names_the_spell(console: Console) -> None:
    console.load("battle-map")
    for button in (console.button.A, console.button.A, console.button.DOWN, console.button.A, console.button.UP):
        console.tap(button)  # move Byuu's party, then onto Fin
        console.emu.run_frames(80)
    console.tap(console.button.A)  # end the phase: an enemy casts, its spell's name and level in a message
    console.emu.run_frames(160)
    assert console.matches_golden("battle-enemy-spell")


def test_dragon_orders_and_its_full_name(console: Console) -> None:
    open_command_window(console)
    for button in (console.button.DOWN, console.button.DOWN, console.button.A):
        console.tap(button)
        console.emu.run_frames(20)
    console.emu.run_frames(40)
    assert console.matches_golden("battle-dragon-orders")  # an 8-letter party name stops at its 8 codes


ROSTER_UNIT = 0x7E21C0  # the roster's first row: Matelite's unit record
UNIT_NAME = 0x11
SON_OF_ZORA = 0x14  # text/fr/names.xml: Fils de Zora, the widest name


def test_the_roster_fits_the_widest_name_and_class(console: Console) -> None:
    console.load("battle-map")
    console.tap(console.button.R)
    console.emu.run_frames(120)
    console.emu.write(ROSTER_UNIT + UNIT_NAME, SON_OF_ZORA)
    console.tap(console.button.A)
    console.emu.run_frames(90)
    assert console.matches_golden("battle-roster")  # Fils de Zora and Garde royal whole, a gap before LV


BG1_SHADOW = 0x7E4000  # the map's BG1 tilemap in WRAM, the windows drawn into it
BG1_MAP_VRAM = 0x4800 * 2  # its VRAM copy, a byte address
BG1_MAP_BYTES = 0x800


def test_command_window_tilemap_goes_up_whole(console: Console) -> None:
    console.load("battle-command-window-upload")  # a unit picked on the map, its command window about to open
    console.tap(console.button.A)
    emu = console.emu
    # the window's slots upload in the same NMI: past a budget, the engine's 2 KB tilemap upload ran out of vblank
    assert bytes(emu.vram_read_range(BG1_MAP_VRAM, BG1_MAP_BYTES)) == bytes(emu.read_range(BG1_SHADOW, BG1_MAP_BYTES))


def test_coup_fatal_list_draws_both_skills_whole(console: Console) -> None:
    console.load("battle-coup-fatal")  # Byuu's command window on Coup fatal
    console.tap(console.button.A)
    console.emu.run_frames(20)
    # Frappe de feu and Frappe vampire on one row: drawn as two lines, each its own slots
    assert console.matches_golden("battle-coup-fatal")


def test_scene_spell_menu_describes_the_spell(console: Console) -> None:
    console.load("battle-scene-spell-menu")  # the combat scene's spell menu, Byuu's Ondes
    for button in (console.button.UP, console.button.DOWN):  # each spell's description, from the messages
        console.tap(button)
        console.emu.run_frames(30)
        assert console.matches_golden(f"battle-scene-spell-{'up' if button == console.button.UP else 'down'}")


def test_combat_scene_spell_banner_names_the_spell_whole(console: Console) -> None:
    console.load("combat-scene-spell-banner")  # a combat scene about to show the cast spell's banner
    console.emu.run_frames(31)
    # the full name, " Nv" for the level icon, the level, centred: it read "Cri striy5"
    assert console.matches_golden("combat-scene-spell-banner")


MDMAEN = 0x00420B
WINDOW_TILEMAP_LATEST = 257 - 13  # a 2 KB DMA takes 13 lines and must end before line 257 (src/vblank.i)


def test_start_menu_tilemap_ends_in_vblank(console: Console) -> None:
    """
    The main loop sends a window's 2 KB tilemap right after the battle NMI, whose panel runs can make it start too late
    to end in vblank: a console a hair slower than ares drops its tail, a menu line cut short (panel_window_tilemap).
    """
    console.load("battle-map-cave")
    emu = console.emu
    sender = symbol("panel_window_tilemap")
    starts: list[int] = []

    def triggered(address: int, value: int) -> None:
        if sender <= emu.get_state().pc < sender + 0x80:
            starts.append(emu.live_counters().v)

    callback = emu.add_write_callback(MDMAEN, MDMAEN, triggered)
    try:
        console.tap(console.button.START)
        emu.run_frames(60)
    finally:
        emu.remove_callback(CallbackKind.WRITE, callback)
    assert starts
    assert max(starts) <= WINDOW_TILEMAP_LATEST
