"""
Scenario 01's organisation screen, from the debug jump: names and classes past their records draw through small_vwf,
on BG3 (the unit's dragon) and BG2 (the party). The equip screens add draw_menu_string's labels and placeholders and
inline labels laid out in fields wider than their text. Infos pages a mid-game party's equipment, a page of new names
at once.
"""

from kintsuki import CallbackKind

from tests.conftest import Console

HDMAEN = 0x00420C
VBLANK = 225  # the first vblank line, no overscan
BG3_MAP = 0x9000  # VRAM bytes: BG3's map at word 0x4800, over its tiles at word 0x4000
BG3_TILES = 0x8000
BG3_SHOWN = 58 * 32  # the map cells a menu shows
BG3_SHADOW = 0x7EC400  # the menu's WRAM copy of BG3's map, which the engine uploads
TILE_2BPP = 16
BG3_SLOT_TILES = [*range(0x280, 0x300), *range(0x1E8, 0x200), *range(0x15, 0x20), *range(0x33, 0x60)]


def test_organisation_names_draw_with_the_small_vwf(console: Console) -> None:
    console.load("menu-organisation")
    names = console.count_calls("menu_draw_fixed_name")
    console.tap(console.button.B)
    console.run_until(lambda: bool(names), limit=1200)
    console.emu.run_frames(90)
    assert console.matches_golden("menu-organisation")


def test_equip_labels_draw_with_the_small_vwf(console: Console) -> None:
    console.load("menu-organisation")
    names = console.count_calls("menu_draw_fixed_name")
    console.tap(console.button.B)
    console.run_until(lambda: bool(names), limit=1200)
    console.emu.run_frames(90)
    console.tap(console.button.UP)
    console.tap(console.button.UP)  # Equiper
    console.tap(console.button.A)  # the party list: NV labels
    console.emu.run_frames(120)
    assert console.matches_golden("menu-party")
    console.tap(console.button.A)  # Byuu: Atk. to Mag. in 8-cell fields, --- placeholders
    console.emu.run_frames(120)
    assert console.matches_golden("menu-equip")


def test_infos_equipment_list_draws_with_the_small_vwf(console: Console) -> None:
    console.load("menu-organisation")
    names = console.count_calls("menu_draw_fixed_name")
    console.tap(console.button.B)
    console.run_until(lambda: bool(names), limit=1200)
    console.emu.run_frames(90)
    for _ in range(3):
        console.tap(console.button.UP)  # Infos
    console.tap(console.button.A)
    console.emu.run_frames(120)
    console.tap(console.button.A)  # the equipment list, its options below
    console.emu.run_frames(120)
    assert console.matches_golden("menu-infos")


def test_infos_page_turn_keeps_the_hdma_on(console: Console) -> None:
    """
    The menu NMI turns HDMA off, drains the engine's DMA queue, and turns it back on; the page's names must queue few
    enough entries for that to end in vblank, or a frame draws without the menu's HDMA (rows unsqueezed, no
    gradient). Entries pile up when the BG3 runs fall back to a cell each (src/menu_vwf.s).
    """
    console.load("menu-infos-page")
    emu = console.emu
    late: list[int] = []

    def enabled(address: int, value: int) -> None:
        line = emu.live_counters().v
        if value and line < VBLANK:
            late.append(line)

    callback = emu.add_write_callback(HDMAEN, HDMAEN, enabled)
    try:
        for _ in range(12):  # down to the page's last row, then onto page 2
            console.tap(console.button.DOWN)
        emu.run_frames(60)
    finally:
        emu.remove_callback(CallbackKind.WRITE, callback)
    assert late == []


def bg3_slot_cells(vram: bytes) -> dict[int, tuple[int, bytes]]:
    """The BG3 cells that show a menu_vwf slot: cell -> (map entry, the tile's pixels)."""
    cells = {}
    for cell in range(BG3_SHOWN):
        entry = int.from_bytes(vram[BG3_MAP + cell * 2 : BG3_MAP + cell * 2 + 2], "little")
        tile = entry & 0x3FF
        if tile in BG3_SLOT_TILES:
            cells[cell] = (entry, vram[BG3_TILES + tile * TILE_2BPP : BG3_TILES + (tile + 1) * TILE_2BPP])
    return cells


def test_infos_page_turn_never_redraws_a_shown_slot(console: Console) -> None:
    """
    Page 2's names reuse page 1's BG3 slots; a slot's pixels may change under a cell that keeps its entry only when the
    shadow holds that entry too (a name of page 2 took the same slot there), or the screen shows page 1's cells over
    page 2's glyphs for a frame (src/menu_vwf.s, retired slots).
    """
    console.load("menu-infos-page")
    emu = console.emu
    redrawn: list[tuple[int, int]] = []
    shown = bg3_slot_cells(bytes(emu.vram_read_range()))

    def frames(count: int) -> None:
        nonlocal shown
        for _ in range(count):
            emu.run_frames(1)
            now = bg3_slot_cells(bytes(emu.vram_read_range()))
            shadow = bytes(emu.read_range(BG3_SHADOW, BG3_SHOWN * 2))
            redrawn.extend(
                (emu.frame_count, cell)
                for cell, (entry, pixels) in now.items()
                if shown.get(cell, (None,))[0] == entry
                and shown[cell][1] != pixels
                and int.from_bytes(shadow[cell * 2 : cell * 2 + 2], "little") != entry
            )
            shown = now

    for _ in range(12):  # down to the page's last row, then onto page 2
        emu.press(0, console.button.DOWN)
        frames(6)
        emu.release(0, console.button.DOWN)
        frames(20)
    frames(60)
    assert redrawn == []
