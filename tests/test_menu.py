"""
Scenario 01's organisation screen, from the debug jump: names and classes past their records draw through small_vwf,
on BG3 (the unit's dragon) and BG2 (the party). The equip screens add draw_menu_string's labels and placeholders and
inline labels laid out in fields wider than their text. Infos pages a mid-game party's equipment, a page of new names
at once.
"""

from collections.abc import Callable

from kintsuki import CallbackKind

from tests.conftest import Console, symbol

MDMAEN = 0x00420B
HDMAEN = 0x00420C
VBLANK = 225  # the first vblank line, no overscan
BG3_MAP = 0x9000  # VRAM bytes: BG3's map at word 0x4800, over its tiles at word 0x4000
BG3_TILES = 0x8000
BG3_SHOWN = 58 * 32  # the map cells a menu shows
BG3_SHADOW = 0x7EC400  # the menu's WRAM copy of BG3's map, which the engine uploads
TILE_2BPP = 16
BG2_SHADOW = 0x7ED400
BG2_TARGET = 0x001868  # nonzero: the BG2 shadow goes to the maps' other copy
BG2_MAPS = ((0xA000, 0xB000), (0xA800, 0xB800))  # VRAM bytes of the BG2 shadow's halves, by BG2_TARGET
MAP_BYTES = 0x1000
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


class ShadowUploads:
    """
    Every write to the tilemap shadows must lie in the span the next upload of its map takes (src/shadow_dirty.s),
    or by the one after: an NMI may fall between a store and its mark. After each upload, VRAM's map must equal the
    shadow.
    """

    def __init__(self, console: Console) -> None:
        self.emu = console.emu
        self.dirty = symbol("shadow_dirty")
        self.written: list[set[int]] = [set(), set()]
        self.late: list[set[int]] = [set(), set()]
        self.unmarked: list[tuple[int, str, int]] = []
        self.torn: list[tuple[int, str, int]] = []
        emu = self.emu
        self.writes = emu.add_write_callback(BG3_SHADOW, BG3_SHADOW + 2 * MAP_BYTES - 1, self.write)
        self.execs = [
            self.exec_at("shadow_trim_bg3", lambda: self.trim(0)),
            self.exec_at("shadow_trim_bg2", self.trim_bg2),
            self.exec_at("menu_vwf._queue_drained", self.drained),
        ]

    def exec_at(self, name: str, hook: Callable[[], None]) -> int:
        address = symbol(name)
        return self.emu.add_exec_callback(address, address, lambda *_: hook())

    def close(self) -> None:
        self.emu.remove_callback(CallbackKind.WRITE, self.writes)
        for callback in self.execs:
            self.emu.remove_callback(CallbackKind.EXEC, callback)

    def write(self, address: int, _: int) -> None:
        offset = address - BG3_SHADOW
        self.written[offset // MAP_BYTES].add(offset % MAP_BYTES)

    def trim(self, layer: int) -> None:
        low, high = self.emu.read16(self.dirty + 4 * layer), self.emu.read16(self.dirty + 4 * layer + 2)
        outside = {offset for offset in self.written[layer] | self.late[layer] if not low <= offset < high}
        name = ("BG3", "BG2")[layer]
        self.unmarked.extend((self.emu.frame_count, name, offset) for offset in sorted(outside & self.late[layer]))
        self.late[layer] = outside - self.late[layer]
        self.written[layer] = set()

    def trim_bg2(self) -> None:
        if self.emu.read16(self.dirty + 12):
            self.trim(1)

    def drained(self) -> None:
        presents = self.dirty + 16
        sent = self.emu.read16(presents)
        self.emu.write_range(presents, bytes(2))
        vram = bytes(self.emu.vram_read_range())
        if sent & 1:
            self.compare("BG3", vram[BG3_MAP : BG3_MAP + MAP_BYTES], BG3_SHADOW)
        if sent & 2:
            for half, start in enumerate(BG2_MAPS[1 if self.emu.read(BG2_TARGET) else 0]):
                self.compare("BG2", vram[start : start + MAP_BYTES // 2], BG2_SHADOW + half * MAP_BYTES // 2)

    def compare(self, name: str, vram: bytes, source: int) -> None:
        shadow = bytes(self.emu.read_range(source, len(vram)))
        offset = next((i for i in range(0, len(vram), 2) if vram[i : i + 2] != shadow[i : i + 2]), None)
        if offset is not None:
            self.torn.append((self.emu.frame_count, name, source - BG3_SHADOW + offset))


def test_trimmed_uploads_leave_the_maps_whole(console: Console) -> None:
    """Through the start menu, Equiper, Infos and a page turn, no shadow write goes unmarked."""
    console.load("menu-organisation")
    emu = console.emu
    uploads = ShadowUploads(console)
    try:
        names = console.count_calls("menu_draw_fixed_name")
        console.tap(console.button.B)
        console.run_until(lambda: bool(names), limit=1200)
        emu.run_frames(90)
        console.tap(console.button.UP)
        console.tap(console.button.UP)  # Equiper
        console.tap(console.button.A)
        emu.run_frames(120)
        console.tap(console.button.A)  # Byuu's equipment
        emu.run_frames(120)
        for _ in range(3):
            console.tap(console.button.B)
            emu.run_frames(60)
        console.tap(console.button.UP)  # Infos
        console.tap(console.button.A)
        emu.run_frames(120)
        console.tap(console.button.A)  # the equipment list
        emu.run_frames(120)
        for _ in range(12):  # down its rows, onto page 2
            console.tap(console.button.DOWN)
        emu.run_frames(60)
    finally:
        uploads.close()
    assert (uploads.unmarked, uploads.torn) == ([], [])


def test_an_idle_menu_sends_a_sweep_slice_a_frame(console: Console) -> None:
    """With nothing drawn, each frame's upload of a tilemap shadow is the 512-byte sweep slice, not the whole 4 KB."""
    console.load("menu-organisation")
    emu = console.emu
    names = console.count_calls("menu_draw_fixed_name")
    console.tap(console.button.B)
    console.run_until(lambda: bool(names), limit=1200)
    emu.run_frames(90)
    console.tap(console.button.UP)
    console.tap(console.button.UP)  # Equiper
    console.tap(console.button.A)
    emu.run_frames(120)
    sizes: list[int] = []

    def fired(_: int, channels: int) -> None:
        for channel in range(8):
            registers = 0x4300 + channel * 0x10
            source = emu.read16(registers + 2) | emu.read(registers + 4) << 16
            if channels >> channel & 1 and BG3_SHADOW <= source < BG3_SHADOW + 2 * MAP_BYTES:
                sizes.append(emu.read16(registers + 5))

    callback = emu.add_write_callback(MDMAEN, MDMAEN, fired)
    try:
        emu.run_frames(60)
    finally:
        emu.remove_callback(CallbackKind.WRITE, callback)
    assert sizes == [0x200] * 60
