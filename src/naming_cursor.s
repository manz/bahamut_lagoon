"""
The naming screen's cursor, after the name being typed.

The vanilla routine (EEDBEE) placed it at 12 pixels a character, the Japanese font's cell. The name is drawn by
draw_string in the dialogue font, so the cursor now goes past the name's real width: each glyph's advance width and
the pixel draw_string leaves after it.
"""

.include "src/expansion.i"

.import "vwf_font"

NAME = 0x7E9E00  ; the name being typed
NAME_X = 0x3A  ; the cursor's x before the first character
CURSOR_X = 0x0010D6  ; the cursor object's x and y offset, as EEDBEE wrote them
CURSOR_Y = 0x0010D8
CURSOR_Y_OFFSET = 0xFFFC
GLYPH_HEIGHT = 16  ; vwf.bin: 16 rows of 1bpp, then the advance width
_length = 0xCC  ; the caller's direct page: characters in the name

.alloc at 0xEEDBEE {
compute_naming_screen_cursor_position:
    jsl.l naming_cursor_position
    rts
}

.alloc naming_cursor in expansion {
naming_cursor_position:
"""Set the cursor object's x to NAME_X plus the name's width in the dialogue font."""
    php
    rep #0x30
    phx
    lda.w #NAME_X
    pha  ; the pen
    ldx.w #0x0000
_next:
    cpx _length
    bcs _done
    phx
    lda.l NAME, x
    and.w #0x00FF
    pha
    asl
    asl
    asl
    asl
    clc
    adc 0x01, s  ; 17 bytes a glyph
    tax
    pla
    lda.l assets_vwf_bin + GLYPH_HEIGHT, x
    and.w #0x00FF
    sec  ; and the pixel after it
    adc 0x03, s
    sta 0x03, s
    plx
    inx
    bra _next
_done:
    pla
    sta.l CURSOR_X
    lda.w #CURSOR_Y_OFFSET
    sta.l CURSOR_Y
    plx
    plp
    rtl
}
