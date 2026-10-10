"""
Item descriptions drawn with the variable-width font.

The description line (feed and item menus) comes from the bank C1 text interpreter at C13470, whose char routine
(C1336D) copies 12x12 glyphs from the original font in bank ED, overwritten by the patch, 12px a char. It now
draws vwf.bin glyphs at a pixel pen into the same line: BG3 2bpp, one 8x16 column per 0x20 bytes from 7E7560
(30 columns), the letter on plane 0 and its shadow (one row down, one pixel right) on plane 1, as vanilla shades
it.
"""


.include "src/expansion.i"
.include "src/wram.i"

.import "vwf_font"
.import "text_buffer_vwf"

; Not written by the debug event, battle, load screen or feed menu runs traced in kintsuki: the end of the
; largest run of WRAM none of them touch (7FD8F0-7FEFFF).
.reserve description_vwf_pen 2 at 0x7FEFF0 in wram
.reserve description_vwf_cell 1 at 0x7FEFF2 in wram  ; the interpreter's char index of the last glyph drawn

DESCRIPTION_LINE = 0x7560  ; bank 7E: column 0 of the description line, 0x20 bytes a column
COLUMN_SIZE = 0x20
GLYPH_HEIGHT = 16
CHAR_INDEX = 0x00  ; the interpreter's char index in its direct page (D = 0): 12px cells from column 0
LINE_WIDTH = 240  ; 30 columns
STRING = 0x5E  ; the interpreter's string pointer in its direct page; Y indexes the current char
LAST_COLUMN = 29  ; the line holds 30 columns; a glyph spills into the next one
WRMPYA = 0x4202
WRMPYB = 0x4203
RDMPY = 0x4216

; Locals, in a stack frame used as the direct page.
LOCALS = 8
_multiplier = 1  ; 0x80 >> (pen & 7): multiplying by it then doubling shifts a glyph row into place
_shadow = 2  ; previous glyph row
_rows = 3
_glyph_row = 4
_letter = 5  ; this row's letter, shifted (word)
_column_word = 7  ; (word)

.alloc description_vwf in expansion {
description_char:
"""Draw char A (8-bit) at the description pen and advance it. Called by the interpreter instead of C1336D."""
    php
    phb
    phd
    sep #0x20
    pha
; A char index that does not follow the last one starts a line: vanilla picked that first cell to centre
; the line at 12px a char, so centre it again at its VWF width.
    lda CHAR_INDEX
    dec
    cmp.l description_vwf_cell
    beq _keep_pen
    rep #0x30
    jsr.w centred_pen
    sta.l description_vwf_pen
_keep_pen:
    sep #0x20
    lda CHAR_INDEX
    sta.l description_vwf_cell
    pla
    rep #0x30
    and.w #0x00FF
    sta 0x10  ; the vanilla routine's own scratch word
    asl
    asl
    asl
    asl
    clc
    adc 0x10
    tax  ; X: the glyph, 17 bytes per char

    tsc
    sec
    sbc.w #LOCALS
    tcs
    tcd
    pea 0x7E7E
    plb
    plb

    lda.l description_vwf_pen
    lsr
    lsr
    lsr
    cmp.w #LAST_COLUMN
    bcc _in_line
    jmp.w _done  ; past the end of the line: draw nothing
_in_line:
    asl
    asl
    asl
    asl
    asl
    clc
    adc.w #DESCRIPTION_LINE
    tay  ; Y: the pen's column
    lda.l description_vwf_pen
    and.w #0x0007
    phx
    tax
    sep #0x20
    lda.l vwf_shift_multipliers, x
    plx
    sta _multiplier
    stz _shadow
    lda #GLYPH_HEIGHT
    sta _rows

_row:
    sep #0x20
    lda.l vwf_font, x
    sta _glyph_row
    jsr.w _shifted  ; plane 0: the letter
    sta _letter
    sep #0x20
    lda _shadow
    lsr
    jsr.w _shifted  ; plane 1: the shadow
    pha
    and.w #0xFF00
    sta _column_word
    lda _letter
    xba
    and.w #0x00FF
    ora _column_word  ; this column: the high halves
    ora.w 0x0000, y
    sta.w 0x0000, y
    pla
    xba
    and.w #0xFF00
    sta _column_word
    lda _letter
    and.w #0x00FF
    ora _column_word  ; the next column: the spill
    ora.w COLUMN_SIZE, y
    sta.w COLUMN_SIZE, y
    sep #0x20
    lda _glyph_row
    sta _shadow
    inx
    iny
    iny
    dec _rows
    bne _row

    rep #0x20
    lda.l vwf_font, x  ; the advance width follows the rows
    and.w #0x00FF
    sec  ; and one pixel of spacing
    adc.l description_vwf_pen
    sta.l description_vwf_pen

_done:
    rep #0x20
    tsc
    clc
    adc.w #LOCALS
    tcs
    pld
    plb
    plp
    rtl

centred_pen:
"""Pen that centres the line starting at [STRING],y: its VWF width up to the next control code (F0 and up)."""
    phy
    stz 0x10
_measure:
    lda [STRING], y
    and.w #0x00FF
    cmp.w #0x00F0
    bcs _measured
    sta 0x12
    asl
    asl
    asl
    asl
    clc
    adc 0x12
    tax
    lda.l vwf_font + GLYPH_HEIGHT, x
    and.w #0x00FF
    sec  ; and one pixel of spacing
    adc 0x10
    sta 0x10
    iny
    bra _measure
_measured:
    ply
    lda.w #LINE_WIDTH
    sec
    sbc 0x10
    bcs _fits
    lda.w #0
_fits:
    lsr
    rts

_shifted:
"""A (8-bit) shifted right by pen & 7, as a 16-bit value with the spill in the low byte. Returns 16-bit A."""
    sta.l WRMPYA
    lda _multiplier
    sta.l WRMPYB
    nop
    nop
    nop
    nop
    rep #0x20
    lda.l RDMPY
    asl
    rts
}

.alloc at 0xC1336D {
    jsr.l description_char
    rts
}
