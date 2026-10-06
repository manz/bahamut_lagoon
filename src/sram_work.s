"""
Extend cart SRAM to 32 KB and clear the pages past the saves at power-on (see sram_work.i).
"""

.include "src/expansion.i"
.include "src/sram_work.i"


; Header SRAM size, log2 KB: 3 (8 KB) -> 5 (32 KB).
.alloc at 0xC0FFD8 {
    .db 0x05
}

; Reset: clc / xce / jml 0xC00000. Clear the work pages on the way.
.alloc at 0xC0FFA2 {
    jml.l clear_sram_work
}

.alloc sram_work_boot in expansion {
clear_sram_work:
"""Zero the pages of banks 21-23, then enter the vanilla reset with the CPU as xce left it (8-bit A and X)."""
    rep #0x30
    lda.w #0x0000
    ldx.w #SRAM_PAGE - 2
_clear:
    sta.l SRAM_WORK_START, x
    sta.l SRAM_WORK_START + 0x010000, x
    sta.l SRAM_WORK_START + 0x020000, x
    dex
    dex
    bpl _clear
    sep #0x30
    jml.l 0xC00000
}
