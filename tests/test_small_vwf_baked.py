"""
Baked strings against the game's own renderer: every long_name_tables name, inline string segment and static battle
string, composed by small_vwf_render from a copy of its codes in WRAM and copied from its baked entry (a name's record,
a segment's id, a static string's address), gives the tiles build.py baked (utils/small_vwf_bake.py), byte for byte:
composed without kerning, as the game's renderer has none, copied kerned on the font's glyphs, as the bake kerns.
"""

from typing import TYPE_CHECKING, Protocol

import pytest
from katsuji.script import Table

from tests.conftest import Console, small_vwf_fields, symbol
from utils.cartridge import rom_offset
from utils.inline_strings import insert_inline_strings
from utils.name_tables import ITEM_TABLE, NAME_TABLES, SMALL_TABLE, encode, read_names
from utils.small_vwf_bake import FONT, MAX_CELLS, MAX_CHARS, TILE, kerning, render

if TYPE_CHECKING:
    from kintsuki import Emu

SCRATCH = 0x7FF000  # WRAM the codes are copied to: off the baked path
STUB = 0x7FF100  # WRAM the calling stub goes to
BAKED_ENTRY = 4
PEN_UNTOUCHED = 0xBEEF  # composing moves small_vwf.pen; a baked copy leaves it


class Renderer(Protocol):
    def __call__(self, source: int, max_cells: int = MAX_CELLS, baked: int = 0) -> tuple[bytes, int]: ...


class Discard:
    """A Writer that keeps nothing: the tests want what insert_text returns, not the bytes."""

    def begin(self) -> None:
        pass

    def write_block_header(self, block: bytes, block_address: int) -> None:
        pass

    def write_block(self, block: bytes, block_address: int) -> None:
        pass

    def end(self) -> None:
        pass


def statics() -> list[tuple[int, bytes]]:
    """The static strings the battle panel draws, at the addresses build.py lays them out at."""
    from build import insert_text

    return insert_text(Discard())[2]


def segments() -> list[bytes]:
    """The inline string segments' codes, by baked id."""
    return insert_inline_strings(Discard(), rom_offset(0xFD0000))[2]


def names() -> list[tuple[str, int, bytes]]:
    table = Table(str(SMALL_TABLE))
    return [
        (f"{name_table.label}[{index}]", name_table.address + index * name_table.record, encode(table, name))
        for name_table in (*NAME_TABLES, ITEM_TABLE)
        for index, name in enumerate(read_names(name_table.source))
    ]


def call(emu: Emu, routine: int) -> None:
    """jsl routine from a stub in WRAM and run to its return. The CPU coroutine is rebuilt first: a savestate stops it
    mid-instruction, and new registers would not take."""
    emu.rearm_cpu()
    state = emu.run_asm(bytes([0x22, *routine.to_bytes(3, "little")]), load_addr=STUB, max_frames=2)
    assert state.pc == emu.EXIT_PC, f"{routine:06X} did not return"


@pytest.fixture(scope="module")
def renderer(console: Console) -> Renderer:
    console.load("menu-organisation")
    small_vwf = symbol("small_vwf")
    fields = small_vwf_fields()[0]
    emu = console.emu

    def render_at(source: int, max_cells: int = MAX_CELLS, baked: int = 0) -> tuple[bytes, int]:
        emu.write_range(small_vwf + fields["source"], source.to_bytes(3, "little"))
        emu.write_range(small_vwf + fields["baked"], baked.to_bytes(2, "little"))
        emu.write(small_vwf + fields["max_chars"], MAX_CHARS)  # a record's redirect sets it too
        emu.write(small_vwf + fields["max_cells"], max_cells)
        call(emu, symbol("small_vwf_render"))
        cells = emu.read(small_vwf + fields["cells"])
        return bytes(emu.read_range(small_vwf + fields["tiles"], cells * TILE)), cells

    return render_at


def test_composed_names_match_the_bake(console: Console, renderer: Renderer) -> None:
    font = FONT.read_bytes()
    for label, _, codes in names():
        console.emu.write_range(SCRATCH, codes + b"\xff")
        for max_cells in (MAX_CELLS, 3):
            assert renderer(SCRATCH, max_cells) == drawn(font, codes, max_cells), (label, max_cells)


def test_baked_names_match_the_bake(renderer: Renderer) -> None:
    font = FONT.read_bytes()
    for label, record, codes in names():
        for max_cells in (MAX_CELLS, 3):
            assert renderer(record, max_cells) == drawn(font, codes, max_cells, kerned=True), (label, max_cells)


def test_inline_segments_match_the_bake(console: Console, renderer: Renderer) -> None:
    font = FONT.read_bytes()
    entries = symbol("small_vwf_inline_baked") & 0xFFFF
    for baked_id, codes in enumerate(segments()):
        console.emu.write_range(SCRATCH, codes + b"\xff")
        for max_cells in (MAX_CELLS, 2):
            assert renderer(SCRATCH, max_cells) == drawn(font, codes, max_cells), (codes, max_cells)
            baked = drawn(font, codes, max_cells, kerned=True)
            assert renderer(SCRATCH, max_cells, entries + baked_id * BAKED_ENTRY) == baked, (codes, max_cells)


def drawn(font: bytes, codes: bytes, max_cells: int, kerned: bool = False) -> tuple[bytes, int]:
    """The bake's tiles as callers read them: the cells drawn, kerned as baked ones are."""
    tiles, cells = render(font, codes, max_cells, kerning(font, [codes]) if kerned else None)
    return tiles[: cells * TILE], cells


def test_static_strings_match_the_bake(console: Console, renderer: Renderer) -> None:
    font = FONT.read_bytes()
    for address, codes in statics():
        console.emu.write_range(SCRATCH, codes + b"\xff")
        assert renderer(SCRATCH) == drawn(font, codes, MAX_CELLS), codes
        pen = symbol("small_vwf") + small_vwf_fields()[0]["pen"]
        console.emu.write_range(pen, PEN_UNTOUCHED.to_bytes(2, "little"))
        assert renderer(address) == drawn(font, codes, MAX_CELLS, kerned=True), (hex(address), codes)
        assert console.emu.read16(pen) == PEN_UNTOUCHED, ("composed, not copied", hex(address), codes)
