"""
The 8x8 variable-width renderer every fixed-cell name goes through.

small_vwf_render packs a string with the katsuji font (assets/small_font.dat, ff4's 8x8 menu font on the 8x8 text
codes) into SMALL_VWF_MAX_CELLS 2bpp tiles, styled as the game's 8x8 font: the letter in colour 1, its shadow one
pixel right and one down in colour 3. Each caller binds the tiles to its own VRAM and tilemap.
"""

.include "src/expansion.i"
.include "src/sram_work.i"


SMALL_VWF_MAX_CELLS = 8
SMALL_VWF_MAX_CHARS = 8
SHADOW_GAP = 1  ; the shadow takes the gap katsuji leaves after a glyph: one more pixel keeps letters apart

; source: the string, FF or FE ends it. max_cells: out of SMALL_VWF_MAX_CELLS. cells: the cells the ink and its
; shadow reach. pen: the pixel column of the next glyph. count, glyph, shift, rows: scratch.
.struct SmallVwf {
    long source
    byte max_chars
    byte max_cells
    byte cells
    byte count
    word pen
    word glyph
    word shift
    byte rows
}

.reserve small_vwf as SmallVwf in sram_work
.reserve small_vwf_text SMALL_VWF_MAX_CHARS + 1 in sram_work
.reserve small_vwf_ink ( SMALL_VWF_MAX_CELLS + 1 ) * 8 in sram_work  ; 1bpp, cell after cell, one spill cell
.reserve small_vwf_tiles SMALL_VWF_MAX_CELLS * 16 in sram_work  ; 2bpp, the output


.alloc small_vwf_code in expansion {
small_vwf_render:
"""
Render small_vwf.source (up to max_chars characters, max_cells cells) into small_vwf_tiles; small_vwf.cells is
how many cells it reaches. Any register sizes; all registers, DB and P are kept.
"""
    php
    phb
    rep #0x30
    pha
    phx
    phy
    jsr.w _copy_text
    pea.w ( SRAM_WORK_START >> 16 ) * 0x0101
    plb
    plb
    jsr.w _clear_ink
    stz.w small_vwf.pen
    ldx.w #0x0000
_next_char:
    sep #0x20
    lda.w small_vwf_text, x
    cmp #0xFF
    beq _shade
    phx
    jsr.w _draw_glyph
    plx
    inx
    bra _next_char
_shade:
    jsr.w _measure
    jsr.w _shade_tiles
    rep #0x30
    ply
    plx
    pla
    plb
    plp
    rtl

_copy_text:
"""Copy the string into small_vwf_text, FF-terminated (FE padding ends it too)."""
    sep #0x20
    lda.l small_vwf.max_chars
    sta.l small_vwf.count
    lda.l small_vwf.source + 2
    pha
    plb
    rep #0x20
    lda.l small_vwf.source
    tay
    sep #0x20
    ldx.w #0x0000
_copy:
    lda.w 0x0000, y
    cmp #0xFE
    bcs _copy_end
    sta.l small_vwf_text, x
    iny
    inx
    lda.l small_vwf.count
    dec
    sta.l small_vwf.count
    bne _copy
_copy_end:
    lda #0xFF
    sta.l small_vwf_text, x
    rts

_clear_ink:
    rep #0x20
    ldx.w #( SMALL_VWF_MAX_CELLS + 1 ) * 8 - 2
_clear:
    stz.w small_vwf_ink, x
    dex
    dex
    bpl _clear
    rts

_draw_glyph:
"""OR glyph A (8-bit) into the ink at the pen, then advance the pen. Glyphs past max_cells are dropped."""
    rep #0x20
    and.w #0x00FF
    sta.w small_vwf.glyph
    asl
    asl
    asl
    clc
    adc.w small_vwf.glyph
    tax  ; X: glyph record, code * 9 (8 rows of 1bpp, then the advance width)
    lda.w small_vwf.pen
    lsr
    lsr
    lsr
    sep #0x20
    cmp.w small_vwf.max_cells
    bcs _no_room
    rep #0x20
    asl
    asl
    asl
    tay  ; Y: ink of the pen's cell
    lda.w small_vwf.pen
    and.w #0x0007
    sta.w small_vwf.shift
    sep #0x20
    lda #0x08
    sta.w small_vwf.rows
_glyph_row:
    lda.l small_font, x
    xba
    lda #0x00
    rep #0x20
    phy
    ldy.w small_vwf.shift
    beq _shifted
_shift:
    lsr
    dey
    bne _shift
_shifted:
    ply
    sep #0x20
    ora.w small_vwf_ink + 8, y  ; spill into the next cell
    sta.w small_vwf_ink + 8, y
    xba
    ora.w small_vwf_ink, y
    sta.w small_vwf_ink, y
    inx
    iny
    dec.w small_vwf.rows
    bne _glyph_row
    lda.l small_font, x  ; the advance width follows the rows
    rep #0x20
    and.w #0x00FF
    clc
    adc.w #SHADOW_GAP
    adc.w small_vwf.pen
    sta.w small_vwf.pen
_no_room:
    rts

_measure:
"""small_vwf.cells: the cells up to the pen's last column plus the shadow's, capped at max_cells."""
    rep #0x20
    lda.w small_vwf.pen
    clc
    adc.w #0x0007 + 1
    lsr
    lsr
    lsr
    sep #0x20
    cmp.w small_vwf.max_cells
    bcc _measured
    lda.w small_vwf.max_cells
_measured:
    sta.w small_vwf.cells
    rts

_shade_tiles:
"""
2bpp tiles from the ink: shadow = (ink >> 1 | ink of the row above) & ~ink; plane 0 = ink | shadow, plane 1 =
shadow.
"""
    sep #0x20
    rep #0x10
    ldx.w #0x0000  ; ink byte
    ldy.w #0x0000  ; tile byte
_shade_byte:
    lda.w small_vwf_ink, x
    lsr
    sta.w small_vwf.glyph
    cpx.w #0x0008
    bcc _no_left
    lda.w small_vwf_ink - 8, x  ; the left cell's last column shades this cell's first
    lsr
    lda #0x00
    ror
    tsb.w small_vwf.glyph
_no_left:
    txa
    and #0x07
    beq _no_above
    lda.w small_vwf_ink - 1, x
    tsb.w small_vwf.glyph
_no_above:
    lda.w small_vwf_ink, x
    trb.w small_vwf.glyph  ; glyph: the shadow
    ora.w small_vwf.glyph
    sta.w small_vwf_tiles, y
    lda.w small_vwf.glyph
    sta.w small_vwf_tiles + 1, y
    iny
    iny
    inx
    cpx.w #SMALL_VWF_MAX_CELLS * 8
    bne _shade_byte
    rts

small_font:
    .incbin "assets/small_font.dat"
}
