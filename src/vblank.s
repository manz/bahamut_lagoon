"""
Where the PPU is in the frame, for the DMAs that must end in vblank with the screen on: the menus' name tiles, a
battle window's tilemap. The latched counters need $4201 bit 7 set, as the game leaves it from boot.
"""

.include "src/expansion.i"
.include "src/vblank.i"

.alloc vblank in expansion {
ppu_line:
"""The PPU's line (16-bit A), from its latched counters. Keeps X and Y."""
    php
    sep #0x20
    lda.l 0x00213F  ; the counters' reads start over
    lda.l 0x002137
    lda.l 0x00213D
    xba
    lda.l 0x00213D
    and #0x01
    xba
    plp
    rtl

dma_fits_vblank:
"""
Carry clear when a DMA of A (16-bit) bytes started now ends before LAST_LINE, at 170 bytes a line (165 with DRAM
refresh, the setup's line over); carry set past it or outside vblank. 16-bit A; keeps X and Y.
"""
    pha
    asl
    clc
    adc 0x01, s
    xba
    and.w #0x00FF
    lsr  ; bytes * 3 / 512
    inc
    sta 0x01, s
    jsl.l ppu_line
    cmp.w #VBLANK_LINE
    bcc _too_late  ; the next frame's lines
    clc
    adc 0x01, s
    cmp.w #LAST_LINE
    pla  ; keeps the carry
    rtl
_too_late:
    pla
    sec
    rtl

await_vblank:
"""Return as a vblank starts (its NMI, if any, taken meanwhile). Keeps A, X and Y."""
    php
    sep #0x20
    pha
_in_vblank:
    lda.l 0x004212
    bmi _in_vblank
_in_display:
    lda.l 0x004212
    bpl _in_display
    pla
    plp
    rtl
}
