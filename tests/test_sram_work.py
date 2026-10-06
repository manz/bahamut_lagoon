"""
The header declares 16 KB of SRAM, and the reset stub zeroes the page past the saves before the game boots.
"""

SAVES = 0x206000
WORK = 0x216000
PAGE = 0x2000


def test_reset_clears_the_work_page_and_keeps_the_saves(console):
    saves = bytes(range(256)) * (PAGE // 256)
    console.emu.inject_sram(saves + b"\xa5" * PAGE)
    console.emu.reset()
    console.emu.run_frames(30)
    assert bytes(console.emu.read_range(WORK, PAGE)) == bytes(PAGE)
    assert bytes(console.emu.read_range(SAVES, PAGE)) == saves
