"""
The 8x8 variable-width renderer every fixed-cell name goes through.

small_vwf_render packs a string with the katsuji font (assets/small_font.dat, ff4's 8x8 menu font on the 8x8 text
codes) into SMALL_VWF_MAX_CELLS 2bpp tiles, styled as the game's 8x8 font: the letter in colour 1, its shadow one
pixel right and one down in colour 3. Each caller binds the tiles to its own VRAM and tilemap.

Handed the record of an 8-byte name table, it draws the full name from long_name_tables (build/gen/long_names.s)
instead of the record's eight codes: build.py renders those names at build time (utils/small_vwf_bake.py), so their
tiles are copied, not composed.
"""

.include "src/expansion.i"
.include "src/sram_work.i"
.extern long_name_tables


SMALL_VWF_MAX_CELLS = 12
SMALL_VWF_MAX_CHARS = 24
; long_name_tables entries: record 0 (long), count (word), pointers (word), record size (byte), baked entries (word)
LONG_NAME_TABLE = 10
; a baked entry, 4 bytes: its tiles' offset in small_vwf_baked_tiles (word), its cells (byte), 0
SHADOW_GAP = 1  ; the shadow takes the gap katsuji leaves after a glyph: one more pixel keeps letters apart

; source: the string, FF or FE ends it. baked: the baked entry of a long_name_tables name, else 0. max_cells: out of
; SMALL_VWF_MAX_CELLS. cells: the cells the ink and its shadow reach; the tiles past them are clear. chars: the
; characters drawn. pen: the pixel column of the next glyph. count, glyph, shift and rows are scratch.
; text: the string, FF-terminated. ink: 1bpp, cell after cell, with a spill cell. tiles: the 2bpp output.
.struct SmallVwf {
    long source
    word baked
    byte max_chars
    byte max_cells
    byte cells
    byte chars
    byte count
    word pen
    word glyph
    word shift
    byte rows
    byte[SMALL_VWF_MAX_CHARS + 1] text
    byte[( SMALL_VWF_MAX_CELLS + 1 ) * 8] ink
    byte[SMALL_VWF_MAX_CELLS * 16] tiles
}

.reserve small_vwf as SmallVwf in sram_work


; build.py's baked tiles (utils/small_vwf_bake.py), offsets in long_name_tables' entries point into them.
.pool small_vwf_baked {
    range 0xFB0000 0xFBFFFF
    strategy order
}

.alloc small_vwf_baked_tiles in small_vwf_baked {
    .incbin "build/gen/small_vwf_baked.bin"
}


.alloc small_vwf_code in expansion {
small_vwf_render:
"""
Render small_vwf.source (up to max_chars characters, max_cells cells) into small_vwf.tiles; small_vwf.cells is
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
    rep #0x20
    lda.w small_vwf.baked
    beq _compose
    jsr.w _copy_baked
    bra _rendered
_compose:
    jsr.w _clear_ink
    stz.w small_vwf.pen
    ldx.w #0x0000
_next_char:
    sep #0x20
    lda.w small_vwf.text, x
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
_rendered:
    rep #0x30
    ply
    plx
    pla
    plb
    plp
    rtl

_copy_text:
"""Copy the string into small_vwf.text, FF-terminated (FE padding ends it too)."""
    jsr.w _redirect
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
    sta.l small_vwf.text, x
    iny
    inx
    lda.l small_vwf.count
    dec
    sta.l small_vwf.count
    bne _copy
_copy_end:
    lda #0xFF
    sta.l small_vwf.text, x
    txa
    sta.l small_vwf.chars
    rts

_redirect:
"""
A record of a long_name_tables table gives its full name: source moves there, max_chars to the maximum, baked to its
entry.
"""
    phb
    phk
    plb
    rep #0x30
    lda.w #0x0000
    sta.l small_vwf.baked
    tax
_table:
    sep #0x20
    lda.w long_name_tables + 2, x
    beq _redirected  ; record 0 at 0x000000 ends the list
    cmp.l small_vwf.source + 2
    bne _next_table
    rep #0x20
    lda.l small_vwf.source
    sec
    sbc.w long_name_tables, x
    bcc _next_table
    jsr.w _record_index
    bcs _next_table  ; not at a record's start
    cmp.w long_name_tables + 3, x
    bcs _next_table
    pha
    asl
    asl
    adc.w long_name_tables + 8, x
    sta.l small_vwf.baked
    pla
    asl
    adc.w long_name_tables + 5, x
    tay
    lda.w 0x0000, y
    sta.l small_vwf.source
    sep #0x20
    phk
    pla
    sta.l small_vwf.source + 2
    lda #SMALL_VWF_MAX_CHARS
    sta.l small_vwf.max_chars
    bra _redirected
_next_table:
    rep #0x20
    txa
    clc
    adc.w #LONG_NAME_TABLE
    tax
    bra _table
_redirected:
    plb
    rts

_record_index:
"""
A: offset into table X (16-bit) -> A: the record, carry clear; carry set past a record's start. The
hardware divider takes the record size.
"""
    sta.l 0x004204
    sep #0x20
    lda.w long_name_tables + 7, x
    sta.l 0x004206
    rep #0x20
    nop  ; the quotient is ready 16 cycles on
    nop
    nop
    nop
    nop
    nop
    nop
    lda.l 0x004216  ; the remainder
    cmp.w #0x0001
    lda.l 0x004214
    rts

_clear_ink:
    rep #0x20
    ldx.w #( SMALL_VWF_MAX_CELLS + 1 ) * 8 - 2
_clear:
    stz.w small_vwf.ink, x
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
    ora.w small_vwf.ink + 8, y  ; spill into the next cell
    sta.w small_vwf.ink + 8, y
    xba
    ora.w small_vwf.ink, y
    sta.w small_vwf.ink, y
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

_copy_baked:
"""The tiles of the baked entry A (16-bit, DB small_vwf's): its cells, max_cells at most, then clear ones."""
    rep #0x30
    tax
    sep #0x20
    lda.l ( long_name_tables & 0xFF0000 ) + 2, x
    cmp.w small_vwf.max_cells
    bcc _baked_cells
    lda.w small_vwf.max_cells
_baked_cells:
    sta.w small_vwf.cells
    rep #0x20
    and.w #0x00FF
    beq _no_baked_tiles
    asl
    asl
    asl
    asl
    dec
    pha  ; the bytes to move, less one
    lda.l long_name_tables & 0xFF0000, x
    clc
    adc.w #small_vwf_baked_tiles & 0xFFFF
    tax
    ldy.w #small_vwf.tiles & 0xFFFF
    pla
    mvn small_vwf_baked_tiles >> 16, small_vwf >> 16
    tya
    sec
    sbc.w #small_vwf.tiles & 0xFFFF
    tay
    bra _clear_tiles
_no_baked_tiles:
    ldy.w #0x0000
    bra _clear_tiles

_shade_tiles:
"""
2bpp tiles from the ink, over the cells it reaches: shadow = (ink >> 1 | ink of the row above) & ~ink; plane 0 =
ink | shadow, plane 1 = shadow. The rest are clear.
"""
    rep #0x30
    lda.w small_vwf.cells
    and.w #0x00FF
    asl
    asl
    asl
    sta.w small_vwf.shift  ; the ink bytes to shade
    sep #0x20
    ldx.w #0x0000  ; ink byte
    ldy.w #0x0000  ; tile byte
    cpx.w small_vwf.shift
    beq _clear_tiles
_shade_byte:
    lda.w small_vwf.ink, x
    lsr
    sta.w small_vwf.glyph
    cpx.w #0x0008
    bcc _no_left
    lda.w small_vwf.ink - 8, x  ; the left cell's last column shades this cell's first
    lsr
    lda #0x00
    ror
    tsb.w small_vwf.glyph
_no_left:
    txa
    and #0x07
    beq _no_above
    lda.w small_vwf.ink - 1, x
    tsb.w small_vwf.glyph
_no_above:
    lda.w small_vwf.ink, x
    trb.w small_vwf.glyph  ; glyph: the shadow
    ora.w small_vwf.glyph
    sta.w small_vwf.tiles, y
    lda.w small_vwf.glyph
    sta.w small_vwf.tiles + 1, y
    iny
    iny
    inx
    cpx.w small_vwf.shift
    bne _shade_byte

_clear_tiles:
"""Clear the tiles from byte Y (16-bit) on."""
    rep #0x20
_clear_tile_word:
    cpy.w #SMALL_VWF_MAX_CELLS * 16
    bcs _tiles_cleared
    lda.w #0x0000
    sta.w small_vwf.tiles, y
    iny
    iny
    bra _clear_tile_word
_tiles_cleared:
    rts

small_font:
    .incbin "assets/small_font.dat"
}
