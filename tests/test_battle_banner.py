"""
The PLAYER PHASE banner, as the game unpacks it when the player's turn starts: the French banners' tiles and tilemap.
"""

from tests.conftest import Console
from utils.banners import french_banner

TILES_VRAM = 0x6000  # BG2's tiles at word 0x3000 while a banner shows
TILEMAP = 0x7EDD00  # E9FD60 builds all four banners' map there


def test_the_player_phase_banner_is_the_french_one(console: Console) -> None:
    console.load("battle-player-phase")
    console.run_until(lambda: console.emu.get_ppu_state().bg12nba >> 4 == 3)
    console.emu.run_frames(12)
    banner = french_banner()
    assert bytes(console.emu.vram_read_range(TILES_VRAM, len(banner.tiles))) == banner.tiles
    assert bytes(console.emu.read_range(TILEMAP, len(banner.tilemap()))) == banner.tilemap()
