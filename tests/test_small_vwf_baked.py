"""
Baked strings against the game's own renderer: every long_name_tables name and inline string segment, composed by
small_vwf_render from a copy of its codes in WRAM and copied from its baked entry (a name's record, a segment's id),
gives the tiles build.py baked (utils/small_vwf_bake.py), byte for byte.
"""

import pytest
from script import Table

from tests.conftest import small_vwf_fields, symbol
from utils.cartridge import rom_offset
from utils.inline_strings import insert_inline_strings
from utils.name_tables import ITEM_TABLE, NAME_TABLES, encode, read_names
from utils.small_vwf_bake import FONT, MAX_CELLS, MAX_CHARS, TILE, render

SCRATCH = 0x7FF000  # WRAM the codes are copied to: off the baked path
STUB = 0x7FF100  # WRAM the calling stub goes to
BAKED_ENTRY = 4


class Discard:
    def write_block(self, data: bytes, address: int) -> None:
        pass


def segments() -> list[bytes]:
    """The inline string segments' codes, by baked id."""
    return insert_inline_strings(Discard(), rom_offset(0xFD0000))[2]


def names() -> list[tuple[str, int, bytes]]:
    table = Table("text/table/mz.tbl")
    return [
        (f"{name_table.label}[{index}]", name_table.address + index * name_table.record, encode(table, name))
        for name_table in (*NAME_TABLES, ITEM_TABLE)
        for index, name in enumerate(read_names(name_table.source))
    ]


def call(emu, routine: int) -> None:
    """jsl routine from a stub in WRAM and run to its return. The CPU coroutine is rebuilt first: a savestate stops it
    mid-instruction, and new registers would not take."""
    emu.rearm_cpu()
    state = emu.run_asm(bytes([0x22, *routine.to_bytes(3, "little")]), load_addr=STUB, max_frames=2)
    assert state.pc == emu.EXIT_PC, f"{routine:06X} did not return"


@pytest.fixture(scope="module")
def renderer(console):
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
        tiles = bytes(emu.read_range(small_vwf + fields["tiles"], MAX_CELLS * TILE))
        return tiles, emu.read(small_vwf + fields["cells"])

    return render_at


def test_composed_names_match_the_bake(console, renderer):
    font = FONT.read_bytes()
    for label, _, codes in names():
        console.emu.write_range(SCRATCH, codes + b"\xff")
        for max_cells in (MAX_CELLS, 3):
            assert renderer(SCRATCH, max_cells) == render(font, codes, max_cells), (label, max_cells)


def test_baked_names_match_the_bake(renderer):
    font = FONT.read_bytes()
    for label, record, codes in names():
        for max_cells in (MAX_CELLS, 3):
            assert renderer(record, max_cells) == render(font, codes, max_cells), (label, max_cells)


def test_inline_segments_match_the_bake(console, renderer):
    font = FONT.read_bytes()
    entries = symbol("small_vwf_inline_baked") & 0xFFFF
    for baked_id, codes in enumerate(segments()):
        console.emu.write_range(SCRATCH, codes + b"\xff")
        for max_cells in (MAX_CELLS, 2):
            expected = render(font, codes, max_cells)
            assert renderer(SCRATCH, max_cells) == expected, (codes, max_cells)
            assert renderer(SCRATCH, max_cells, entries + baked_id * BAKED_ENTRY) == expected, (codes, max_cells)
