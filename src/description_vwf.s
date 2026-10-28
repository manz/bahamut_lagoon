"""
Item descriptions drawn with the variable-width font.

The description line (feed and item menus) comes from the bank C1 text interpreter at C13470, whose char routine
(C1336D) copies 12x12 glyphs from the original font in bank ED, overwritten by the patch, 12px a char. It now
draws vwf.bin glyphs at a pixel pen into the same line: BG3 2bpp, one 8x16 column per 0x20 bytes from 7E7560
(30 columns), the letter on plane 0 and its shadow (one row down, one pixel right) on plane 1, as vanilla shades
it.

The combat scene's spell banner goes through it too (template C1DB21: F6 the spell, F3 78 the level icon, F9 the
level): F6 draws the spell's full name from long_name_tables, not its 8-code record, the icon (glyph 0x78 of page 3)
draws " Nv.", and a line is centred at the width those take.
"""


.include "src/expansion.i"
.include "src/wram.i"

.include "src/name_tables.i"
.import "vwf_font"
.import "text_buffer_vwf"
.extern long_name_tables

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
PAGE = 0x64  ; the interpreter's glyph page (F0-F3 set it for the next char)
PAGE_CODES = 0xF0  ; F0-F3: the next char from page 0-3
LEVEL_PAGE = 3
LEVEL_ICON = 0x78  ; page 3's "Lv"
SPELL_CODE = 0xF6  ; F6 id: a spell's name
NUMBER_CODE = 0xF9  ; F9 word: a number, no leading zeros
LAST_PAGE_CODE = 0xF3
DIGIT_ZERO = 0xAF
BLANK = 0xEF
LETTER_N = 0xC6
LETTER_V = 0x75
PERIOD = 0xA4
SPELL_RECORDS = 0xEF5920  ; the spells' 8-code names: long_name_tables has their full names
END = 0xFF

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
"""
Draw char A (8-bit) at the description pen and advance it, page 3's level icon as " Nv.". Called by the interpreter
instead of C1336D.
"""
    php
    phb
    phd
    sep #0x20
    pha
    jsr.w _line_pen
    lda PAGE
    cmp #LEVEL_PAGE
    bne _plain
    lda 0x01, s
    cmp #LEVEL_ICON
    bne _plain
    pla
    lda #BLANK
    jsr.w _glyph
    lda #LETTER_N
    jsr.w _glyph
    lda #LETTER_V
    jsr.w _glyph
    lda #PERIOD
    jsr.w _glyph
    bra _drawn
_plain:
    pla
    jsr.w _glyph
_drawn:
    pld
    plb
    plp
    rtl

_line_pen:
"""
A char index that does not follow the last one starts a line: vanilla picked that first cell to centre the line at
12px a char, so centre it again at its VWF width. Y: the interpreter's, on the line's first byte. Returns 8-bit A.
"""
    sep #0x20
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
    rts

description_spell_name:
"""
F6's spell (A, 8-bit; Y on it): its full name, a char at a time as the vanilla copy drew the record's eight. Jumped to
from C13582 with the interpreter's return address on the stack; leaves through its ply / rts.
"""
    sep #0x20
    phy
    pha
    dey  ; a line the name starts is measured from its F6
    jsr.w _line_pen
    pla
    rep #0x30
    and.w #0x00FF
    jsr.w _spell_name
    sep #0x20
_name_char:
    lda.l long_name_tables & 0xFF0000, x
    cmp #END
    beq _name_done
    phx
    jsl.l description_char
    plx
    inc CHAR_INDEX
    inx
    bra _name_char
_name_done:
    jml 0xC13548  ; ply / rts

_spell_name:
"""X: spell A's (16-bit) full name, in long_name_tables' bank. 16-bit A, X, Y."""
    asl
    sta 0x12
    ldx.w #0x0000
_find_spells:
    lda.l long_name_tables + LongNameTable.record, x
    cmp.w #SPELL_RECORDS & 0xFFFF
    beq _spells
    txa
    clc
    adc.w #LongNameTable.__size
    tax
    bra _find_spells
_spells:
    lda.l long_name_tables + LongNameTable.pointers, x
    clc
    adc 0x12
    tax
    lda.l long_name_tables & 0xFF0000, x
    tax
    rts

_glyph:
"""Draw char A (8-bit) at the description pen and advance it."""
    php
    phb
    phd
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
    rts

centred_pen:
"""
Pen that centres the line starting at [STRING],y: its VWF width up to the next control code, F6's spell names, F0-F3's
paged chars and F9's numbers counted as drawn.
"""
    phy
    stz 0x10
_measure:
    lda [STRING], y
    and.w #0x00FF
    cmp.w #PAGE_CODES
    bcs _control
    jsr.w _add_advance
    iny
    bra _measure
_control:
    cmp.w #LAST_PAGE_CODE + 1
    bcs _not_paged
    pha  ; the page code
    iny
    lda [STRING], y
    and.w #0x00FF
    tax
    pla
    cmp.w #PAGE_CODES + LEVEL_PAGE
    bne _paged
    cpx.w #LEVEL_ICON
    bne _paged
    lda.w #BLANK
    jsr.w _add_advance
    lda.w #LETTER_N
    jsr.w _add_advance
    lda.w #LETTER_V
    jsr.w _add_advance
    lda.w #PERIOD
    bra _paged_char
_paged:
    txa
_paged_char:
    jsr.w _add_advance
    iny
    bra _measure
_not_paged:
    cmp.w #SPELL_CODE
    bne _not_spell
    iny
    lda [STRING], y
    and.w #0x00FF
    phy
    jsr.w _spell_name
_spell_width:
    lda.l long_name_tables & 0xFF0000, x
    and.w #0x00FF
    cmp.w #END
    beq _spell_measured
    phx
    jsr.w _add_advance
    plx
    inx
    bra _spell_width
_spell_measured:
    ply
    iny
    bra _measure
_not_spell:
    cmp.w #NUMBER_CODE
    bne _measured
    iny
    lda [STRING], y
    iny
    iny
    phy
    ldy.w #0x0001  ; its digits
_digits:
    cmp.w #10
    bcc _counted
    jsr.w _tenth
    iny
    bra _digits
_counted:
    lda.w #DIGIT_ZERO
    jsr.w _add_advance
    dey
    bne _counted
    ply
    jmp.w _measure
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

_add_advance:
"""0x10 += char A's (16-bit) advance and one pixel of spacing. Keeps Y."""
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
    sec
    adc 0x10
    sta 0x10
    rts

_tenth:
"""A /= 10 (16-bit), by subtraction: only to count a number's digits."""
    ldx.w #0x0000
_subtract:
    cmp.w #10
    bcc _quotient
    sbc.w #10  ; carry set: no borrow
    inx
    bra _subtract
_quotient:
    txa
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

.alloc at 0xC13582 {
    jml.l description_spell_name
}
