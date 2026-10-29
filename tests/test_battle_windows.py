"""
Scenario 00's player phase on the battle map: the command window, and a unit's skill list after moving, are BG1
windows whose strings draw through small_vwf into the window font. So is the START menu, whose strings outgrow
their Japanese character counts but not their cells. A later map's START menu checks its tilemap's DMA timing. Bouger's shadow tiles BG3 with codes the panel keeps clear. So are a sky map's clouds.
"""

import re
from pathlib import Path

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


def test_whole_side_target_reads_tous(console: Console) -> None:
    console.load("battle-scene-spell-menu")
    for button in (console.button.B, console.button.DOWN, console.button.A):  # back to the commands, to Objet
        console.tap(button)
        console.emu.run_frames(30)
    for _ in range(7):  # Herbe de feu, which hits every enemy
        console.tap(console.button.DOWN)
        console.emu.run_frames(12)
    console.tap(console.button.A)
    console.emu.run_frames(40)
    # the target window read 全体, two kanji tiles
    assert console.matches_golden("combat-scene-all-targets")


def test_combat_scene_spell_banner_names_the_spell_whole(console: Console) -> None:
    console.load("combat-scene-spell-banner")  # a combat scene about to show the cast spell's banner
    console.emu.run_frames(31)
    # the full name, " Nv." for the level icon, the level, centred: it read "Cri striy5"
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


PANEL_SOURCE = Path("src/battle_panel_vwf.s")
PANEL_FONT_TILE = 0x200  # BG3 tile of the panel font's code 0
FONT_VRAM_BYTES = 0x8000  # its pixels, a byte address


def panel_pool_codes() -> set[int]:
    """The 8x8 codes the panel's slots draw over: _pool_runs up to the windows'."""
    runs = PANEL_SOURCE.read_text().split("_pool_runs:")[1].split("; the windows'")[0]
    return {
        code
        for first, length in re.findall(r"\.db (0x[0-9A-F]+), (\d+)", runs)
        for code in range(int(first, 16), int(first, 16) + int(length))
    }


def test_the_move_range_shadow_keeps_its_tiles(console: Console) -> None:
    """Bouger darkens the map out of reach with BG3 tiles of the panel font (0x2C, 0x2E): a panel slot on one
    tiles the whole shadow with the text it last drew."""
    open_command_window(console)
    console.tap(console.button.A)  # Bouger
    console.emu.run_frames(90)
    tilemap = (console.emu.get_ppu_state().bg3sc >> 2) << 10
    words = bytes(console.emu.vram_read_range(tilemap * 2, 0x800))
    shadow = {(words[2 * cell] | words[2 * cell + 1] << 8) & 0x3FF for cell in range(0x400)}
    assert shadow == {PANEL_FONT_TILE + 0x2C, PANEL_FONT_TILE + 0x2E}
    assert not {tile - PANEL_FONT_TILE for tile in shadow} & panel_pool_codes()


MAP_FONT_TILES = range(0x01, 0x24)  # 8x8 codes a sky map loads its clouds over, BG3 tiling the sky with them


def test_a_sky_map_keeps_its_clouds(console: Console) -> None:
    console.load("battle-sky-map")  # a battle over the clouds about to start, the panel yet to draw
    vram = FONT_VRAM_BYTES + MAP_FONT_TILES.start * 16
    clouds = bytes(console.emu.vram_read_range(vram, len(MAP_FONT_TILES) * 16))
    lines = console.count_calls("panel_put_char_hook")
    for _ in range(60):
        console.tap(console.button.A)
    assert lines
    assert bytes(console.emu.vram_read_range(vram, len(MAP_FONT_TILES) * 16)) == clouds


def open_terrain_spells(console: Console) -> None:
    console.load("battle-map-cave")
    for button in (console.button.R, console.button.R, console.button.A, console.button.DOWN, console.button.A):
        console.tap(button)  # Yoyo's squad, Terrain
        console.emu.run_frames(40)
    console.tap(console.button.A)  # Magie mixte: a spell list, each row a name, its level and its MP
    console.emu.run_frames(60)


def test_spell_list_rows_show_the_level(console: Console) -> None:
    open_terrain_spells(console)
    # Nv and the level past the name: the battle message's icon hook had dropped them
    assert console.matches_golden("battle-terrain-spells")


def test_spell_description_draws_at_once(console: Console) -> None:
    open_terrain_spells(console)
    transfers = console.count_calls("battle_dma_transfer")
    console.tap(console.button.RIGHT)  # Regard de feu: its description, drawn as the cursor moves
    assert not transfers  # a char a time took a vblank each: half a second a move
    assert console.matches_golden("battle-terrain-spell-description")


LIST_START = 0xC0D640  # C0D640: a spell list's rows, $C2 the first entry, $C3 how many
LIST_COUNT = 0x7E01C3
LIST_FIRST = 0x7E01C2
LIST_ENTRIES = 0x7E0010  # 2 bytes an entry: the spell, its level
WIDEST_SPELLS = (0xB4, 0xD4, 0x44, 0xE4, 0x9E, 0xEB, 0x23, 0x82)  # Lancer de lancier, Jugement céleste...
LEVELS = (40, 7, 99, 1)


def test_a_full_spell_list_draws_every_row_whole(console: Console) -> None:
    """Eight of the widest names, two-digit levels: their rows outgrow the panel's slots, the list borrows the battle
    message's first line."""
    console.load("battle-map-cave")
    for button in (console.button.R, console.button.R, console.button.A, console.button.DOWN, console.button.A):
        console.tap(button)
        console.emu.run_frames(40)
    emu = console.emu

    def fill(address: int, value: int = 0) -> None:
        emu.write(LIST_COUNT, len(WIDEST_SPELLS))
        entries = LIST_ENTRIES + emu.read(LIST_FIRST) * 4
        for index, spell in enumerate(WIDEST_SPELLS):
            emu.write_range(entries + 2 * index, bytes([spell, LEVELS[index % len(LEVELS)]]))

    callback = emu.add_exec_callback(LIST_START, LIST_START, fill)
    try:
        console.tap(console.button.A)
        emu.run_frames(60)
    finally:
        emu.remove_callback(CallbackKind.EXEC, callback)
    assert console.matches_golden("battle-terrain-spells-full")


PANEL_TILEMAP = 0x7EC000  # C0E38D's DMA source: the panel's BG3 tilemap
WINDOW_TILEMAP = 0x7E4000  # C0AA9E's DMA source: a window's tilemap
WINDOW_RUNS = 0x38  # the windows' runs in panel.dirty
PANEL_RUNS = 0x07  # panel.dirty: the panel's runs and the spell list's


def test_the_panel_tilemap_goes_up_after_its_slots(console: Console) -> None:
    """
    The main loop draws the panel's lines over lag frames, whose NMIs leave the slots behind: the tilemap sent first
    showed the roster's names in the list's rows, and back (panel_bg3_tilemap).
    """
    console.load("battle-map-cave")
    for button in (console.button.R, console.button.R, console.button.A, console.button.DOWN, console.button.A):
        console.tap(button)
        console.emu.run_frames(40)
    emu = console.emu
    dirty = symbol("panel.dirty")
    pending: list[int] = []

    def sent(address: int, value: int) -> None:
        source = emu.read(0x004302) | emu.read(0x004303) << 8 | emu.read(0x004304) << 16
        if value & 1 and source == PANEL_TILEMAP:
            pending.append(emu.read(dirty) & PANEL_RUNS)

    callback = emu.add_write_callback(MDMAEN, MDMAEN, sent)
    try:
        for button in (console.button.A, console.button.B):  # the spell list, then the roster again
            console.tap(button)
            emu.run_frames(60)
    finally:
        emu.remove_callback(CallbackKind.WRITE, callback)
    assert pending
    assert not any(pending)


def test_a_window_tilemap_goes_up_after_its_slots(console: Console) -> None:
    """
    An enemy unit's notice: its text is drawn in the window's slots before C0AA9E sends the tilemap, which went up
    first and showed what the slots held before for a few frames (panel_window_tilemap).
    """
    console.load("battle-map-cave")
    for button in (console.button.UP,) * 4 + (console.button.LEFT,):
        console.tap(button)
        console.emu.run_frames(12)
    emu = console.emu
    dirty = symbol("panel.dirty")
    pending: list[int] = []

    def sent(address: int, value: int) -> None:
        source = emu.read(0x004302) | emu.read(0x004303) << 8 | emu.read(0x004304) << 16
        if value & 1 and source == WINDOW_TILEMAP:
            pending.append(emu.read(dirty) & WINDOW_RUNS)

    callback = emu.add_write_callback(MDMAEN, MDMAEN, sent)
    try:
        console.tap(console.button.A)  # Unité ennemie.
        emu.run_frames(30)
    finally:
        emu.remove_callback(CallbackKind.WRITE, callback)
    assert pending
    assert not any(pending)


def test_the_skill_window_fits_magie_blanche(console: Console) -> None:
    console.load("battle-map-cave")
    for button in (console.button.R, console.button.A, console.button.DOWN, console.button.A):
        console.tap(button)  # Sendak's squad, Terrain
        console.emu.run_frames(40)
    # Magie blanche (59 pixels) took 6 cells: the window grows a tile left, the names take the cursor's blank
    assert console.matches_golden("battle-terrain-kinds")


def test_a_closed_window_gives_its_slots_back(console: Console) -> None:
    """Sendak's Terrain window, then back to the map: its rows kept their slots, never drawn again, and the START menu
    after it ran out, Mode audio blank."""
    console.load("battle-map-cave")
    for button in (console.button.R, console.button.A, console.button.DOWN, console.button.A, console.button.B):
        console.tap(button)
        console.emu.run_frames(40)
    for button in (console.button.B, console.button.START):
        console.tap(button)
        console.emu.run_frames(60)
    assert console.matches_golden("battle-start-menu-after-commands")
