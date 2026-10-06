"""
Cart SRAM past the saves, as a bss pool for state no game engine touches.

The board maps SRAM at 20-3F:6000-7FFF, one 8 KB page per bank modulo the size the header declares. The vanilla
header says 8 KB, all of it save files (bank 20). sram_work.s raises it to 16 KB, which gives bank 21 its own page;
bank 22 mirrors 20 again. The page holds no save data: the reset stub zeroes it at power-on.
"""


SRAM_WORK_START := 0x216000
SRAM_WORK_END := 0x217FFF

.pool sram_work {
    bss
    range SRAM_WORK_START SRAM_WORK_END
    strategy order
}
