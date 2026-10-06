"""
Extend cart SRAM to 16 KB and clear the page past the saves at power-on (see sram_work.i).
"""

.include "src/expansion.i"
.include "src/sram_work.i"


; Header SRAM size, log2 KB: 3 (8 KB) -> 4 (16 KB).
.alloc at 0xC0FFD8 {
    .db 0x04
}

; Reset: clc / xce / jml 0xC00000. Clear the work page on the way.
.alloc at 0xC0FFA2 {
    jml.l clear_sram_work
}

.alloc sram_work_boot in expansion {
clear_sram_work:
"""Zero SRAM_WORK_START-SRAM_WORK_END, then enter the vanilla reset with the CPU as xce left it (8-bit A and X)."""
    rep #0x30
    lda.w #0x0000
    ldx.w #SRAM_WORK_END - SRAM_WORK_START - 1
_clear:
    sta.l SRAM_WORK_START, x
    dex
    dex
    bpl _clear
    sep #0x30
    jml.l 0xC00000
}
