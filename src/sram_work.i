"""
Cart SRAM past the saves, as a bss pool for state no game engine touches.

The board maps SRAM at 20-3F:6000-7FFF, one 8 KB page per bank modulo the size the header declares. The vanilla
header says 8 KB, all of it save files (bank 20). sram_work.s raises it to 32 KB, which gives banks 21-23 their own
pages; bank 24 mirrors 20 again. Pool ranges stay within a bank: sram_work is bank 21, sram_menu bank 22, bank 23 is
spare. The pages hold no save data: the reset stub zeroes them at power-on.
"""


SRAM_WORK_START := 0x216000
SRAM_WORK_END := 0x217FFF
SRAM_MENU_START := 0x226000
SRAM_MENU_END := 0x227FFF
SRAM_PAGE := 0x2000
SRAM_EXTRA_PAGES := 3  ; banks 21-23

.pool sram_work {
    bss
    range SRAM_WORK_START SRAM_WORK_END
    strategy order
}

.pool sram_menu {
    bss
    range SRAM_MENU_START SRAM_MENU_END
    strategy order
}
