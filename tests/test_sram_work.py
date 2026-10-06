"""
The header declares 32 KB of SRAM, and the reset stub zeroes the pages past the saves before the game boots.
"""

SAVES = 0x206000
WORK_PAGES = (0x216000, 0x226000, 0x236000)
PAGE = 0x2000


def test_reset_clears_the_work_pages_and_keeps_the_saves(console):
    saves = bytes(range(256)) * (PAGE // 256)
    console.emu.inject_sram(saves + b"\xa5" * PAGE * len(WORK_PAGES))
    console.emu.reset()
    console.emu.run_frames(30)
    for page in WORK_PAGES:
        assert bytes(console.emu.read_range(page, PAGE)) == bytes(PAGE)
    assert bytes(console.emu.read_range(SAVES, PAGE)) == saves
