"""
The attract mode's staff credits (room 250) draw their own charset (text/table/intro.tbl: a-z from 0x01, A-Z from
0x1D) with the 8x16 font at E8:CD55: the French credits are encoded with it, not with the dialog table, whose codes
draw noise tiles there.
"""

from pathlib import Path

from script import Table

from utils.cartridge import rom_offset
from utils.credits import STEP, TABLE
from utils.dump_rooms import decompress_block
from utils.ips import apply_ips

REPO = Path(__file__).resolve().parents[1]
ROM = REPO / "build/bl.sfc"
IPS = REPO / "build/bl.ips"
ROOM_POINTERS = 0xDA8000
CREDITS_ROOM = 250


def room(path: Path, room_id: int) -> bytes:
    """Room room_id's script, decompressed from wherever its pointer leads."""
    with path.open("rb") as rom:
        rom.seek(rom_offset(ROOM_POINTERS) + room_id * 3)
        rom.seek(rom_offset(int.from_bytes(rom.read(3), "little")))
        return bytes(decompress_block(rom))


def spelled(word: str) -> bytes:
    """`word` as the room spells it, a step before each character."""
    return Table(str(REPO / TABLE)).to_bytes("".join(STEP + character for character in word))


def test_the_credits_are_french_in_their_charset(tmp_path: Path) -> None:
    patched = tmp_path / "bl.sfc"
    patched.write_bytes(apply_ips(ROM.read_bytes(), IPS.read_bytes()))
    script = room(patched, CREDITS_ROOM)
    assert (spelled("directeur") in script, spelled("director") in script) == (True, False)
