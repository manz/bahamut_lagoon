"""
The naming screen's cursors: after the name being typed, and on the page labels.

The vanilla routine (EEDBEE) placed it at 12 pixels a character, the Japanese font's cell. The name is drawn by
draw_string in the dialogue font, so the cursor now goes past the name's real width: each glyph's advance width and
the pixel draw_string leaves after it.

The page cursor (EED7D9) stopped every 48 pixels, the Japanese labels' spacing; it now stops at each French label
(text/inline.xml places them, cells 0 8 16 21 from x 56), 4 pixels before it.
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
_page = 0xC0  ; the caller's direct page: the label under the page cursor, 0-3
PAGE_CURSOR_X = 0x001056  ; the page cursor object's x and y
PAGE_CURSOR_Y = 0x001058
PAGE_CURSOR_ROW = 0x14

.alloc at 0xEED7D9 {
place_page_cursor:
"""The page cursor at its label: Majuscules, Minuscules, Autre, Fin."""
    php
    rep #0x30
    phx
    lda _page
    asl
    tax
    lda.l page_cursor_x, x
    sta.l PAGE_CURSOR_X
    lda.w #PAGE_CURSOR_ROW
    sta.l PAGE_CURSOR_Y
    plx
    plp
    rts
}

.alloc at 0xEEDBEE {
compute_naming_screen_cursor_position:
    jsl.l naming_cursor_position
    rts
}

.alloc naming_cursor in expansion {
page_cursor_x:
    .dw 52, 116, 180, 220

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
