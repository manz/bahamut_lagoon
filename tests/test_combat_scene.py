"""
The combat scene's names row (savestate a few presses before Sendak's party meets Rhadamanthe): the active character's
name turns yellow through its own slots, not the font's yellow copy (kana for French codes), and no other string, the
command list or a target window, takes the slots a name still shows (src/c1_vwf.s).
"""

from tests.conftest import Console, symbol

NAMES_ROW = 0x7E4800 + 3 * 0x40  # the C1 shadow's row of the party's names
COLUMNS = 32
YELLOW_KANA = range(0xD3, 0x100)  # the yellow copy of the kana tiles the slots 0x33-0x5F replace
OWNER_CELL = 0x7FFF  # slot_owner without its yellow bit
# the scene opens; then Sendak attacks, Melody picks a spell list and backs out, the cursor moves on
PRESSES = ("A", "A", "DOWN", "A", "B", "B", "RIGHT", "A", "B", "B")


def _slot(tile: int) -> int | None:
    if 0x33 <= tile < 0x60:
        return tile - 0x33
    if 0x170 <= tile < 0x180:
        return tile - 0x170 + 45
    if 0x100 <= tile < 0x16C:
        return tile - 0x100 + 61
    return None


def _wrong_cells(console: Console) -> list[tuple[int, int]]:
    """Names row cells showing yellow kana or a slot another cell owns: (column, tile)."""
    emu = console.emu
    owners = symbol("c1.slot_owner")
    wrong = []
    for column in range(COLUMNS):
        cell = NAMES_ROW + column * 2
        tile = emu.read16(cell) & 0x3FF
        slot = _slot(tile)
        if tile in YELLOW_KANA or (
            slot is not None and emu.read16(owners + slot * 2) & OWNER_CELL != cell - 0x7E4800 + 1
        ):
            wrong.append((column, tile))
    return wrong


def test_combat_scene_names_keep_their_slots(console: Console) -> None:
    console.load("combat-scene-before")
    console.emu.run_frames(500)  # into the scene: the names row drawn, Sendak's in yellow
    assert _wrong_cells(console) == []
    for name in PRESSES:
        console.tap(getattr(console.button, name))
        assert _wrong_cells(console) == [], name
