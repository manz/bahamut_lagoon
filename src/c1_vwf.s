"""
The C1 engine's strings through small_vwf: the dragon feed menu's item list and header.

C12EC0 copies a name (A: id; Y: 0 characters, 1 enemies, 2 spells, 3 items, 4 dragons) into a buffer at 7E0870,
then C12DDA draws a string from [$5E] at the cell C12E49 computed (X, in the tilemap shadow at 7E4800, BG2 here): a
cell a character, tile = C1CB4B[code] | 0x3800 (an item's icon too), the row above for kana dakuten marks. C12EC0 leaves
the name's record here, so that the draw renders the record (and its full name) rather than the buffer's eight
characters.

A string of three characters or more renders; its cells take slots: the font's kana (tiles 0x33-0x5F, which only
kana codes map to), the blank tiles 0x170-0x17F, then the graphics at 0x100-0x16F this screen does not show (the
engine loads the font again with each screen), over the 4bpp font the engine loads at VRAM 0x4000 (the glyph
over the window background, colour 4). A slot belongs to a shadow cell and is free again once that cell shows
something else. Changed slots mark their run dirty; the engine's shadow upload callback (C109A4) carries the dirty
runs first.
"""

.include "src/expansion.i"
.include "src/sram_work.i"
.extern small_vwf_render
.extern small_vwf


C1_SHADOW = 0x7E4800
C1_SHADOW_CELLS = 0x400
C1_FONT_VRAM = 0x4000
C1_TILE_MAP = 0xC1CB4B  ; code -> tile
C1_ATTR = 0x3800
C1_BLANK_TILE = 0x12
C1_BUFFER = 0x000870  ; where C12EC0 copies a name
C1_SLOTS = 173
C1_KANA_SLOTS = 45  ; tiles 0x33-0x5F, then 0x170-0x17F, then 0x100-0x16F
C1_BLANK_SLOTS = 16
C1_TILE_4BPP = 32
C1_TILE_2BPP = 16
C1_MIN_CHARS = 3
C1_MAX_CELLS = 12
C1_ITEM_RECORDS = 0xEF3CA0
C1_NO_RECORD = 0xFF

; slot_owner: the shadow cell a slot draws, plus 1; 0 when free (cells are even). type: the name type C12EC0 copied,
; C1_NO_RECORD when none; id its id. field: the cells the engine's draw covers. index: 1 when an icon came first.
; dirty: a bit per run. The rest is scratch.
.struct C1Vwf {
    byte[C1_SLOTS * C1_TILE_4BPP] tiles
    word[C1_SLOTS] slot_owner
    word type
    word id
    word field
    word cell
    word index
    word slot
    word rows
    word key
    byte plane
    byte dirty
    byte changed
}

.reserve c1 as C1Vwf in sram_c1


; C12EC0: sep #0x20 / pha / lda #0x70.
.alloc at 0xC12EC0 {
    jml.l c1_name_copy
}

; C12DDA, past the cell C12E49 computed: tdc / tay / lda [$5E], y.
.alloc at 0xC12DDF {
    jml.l c1_draw_string
}

; The quantity counter after the counts, the kana コ, is blank now (its tile is a slot): a code at C17642 (lda #0x3D /
; jsr C12E94), a tile at C19D4D and C19D65 (lda #0x3D / jsr C12EB4).
.alloc at 0xC17643 {
    .db 0xEF
}
.alloc at 0xC19D4E {
    .db C1_BLANK_TILE
}
.alloc at 0xC19D66 {
    .db C1_BLANK_TILE
}

; C109A4, the shadow upload callback: sep #0x20 / lsr $3C.
.alloc at 0xC109A4 {
    jsl.l c1_upload
}


.alloc c1_vwf in expansion {
c1_name_copy:
"""Remember the name C12EC0 copies (A: id, Y: type), then copy it as the engine does."""
    php
    rep #0x30
    pha
    and.w #0x00FF
    sta.l c1.id
    tya
    sta.l c1.type
    pla
    plp
    sep #0x20
    pha
    lda #0x70
    jml.l 0xC12EC5

c1_draw_string:
"""
X: the first cell. Draws [$5E] through small_vwf when it has three characters or more; Y and $10 end on the
character count, X past the string, as the engine leaves them; P as it came.
"""
    php
    rep #0x30
    phx
    jsr.w _string_source
    jsr.w _field_cells
    plx
    sep #0x20
    lda.l c1.field
    cmp #C1_MIN_CHARS
    bcc _vanilla
    jsr.w _item_icon
    lda.l c1.field
    sta.l small_vwf.max_chars
    cmp #C1_MAX_CELLS + 1
    bcc _cells
    lda #C1_MAX_CELLS
_cells:
    sta.l small_vwf.max_cells
    jsl.l small_vwf_render
    jsr.w _draw_cells
    rep #0x30
    lda.w #C1_NO_RECORD
    sta.l c1.type
    lda.l c1.field
    clc
    adc.l c1.index  ; the icon, if any
    tay
    plp
    jml.l 0xC12E04  ; sty $10 / rts
_vanilla:
    rep #0x30
    lda.w #C1_NO_RECORD
    sta.l c1.type
    plp
    tdc
    tay
    jml.l 0xC12DE1

_string_source:
"""small_vwf.source: [$5E], or the record of the name C12EC0 just copied there (enemies, spells, items)."""
    lda.b 0x5E
    sta.l small_vwf.source
    lda.b 0x60
    and.w #0x00FF
    sta.l small_vwf.source + 2
    lda.l c1.type
    cmp.w #1
    bcc _own_source
    cmp.w #4 + 1
    bcs _own_source
    lda.b 0x5E
    cmp.w #C1_BUFFER & 0xFFFF
    bne _own_source
    lda.l c1.type
    asl
    tax
    lda.l c1.id
    and.w #0x00FF
    sta.l c1.cell
    asl
    asl
    asl  ; id * 8
    cpx.w #3 * 2
    bne _not_item
    clc
    adc.l c1.cell  ; id * 9: an item's record, its icon first
_not_item:
    clc
    adc.l _record_tables, x
    sta.l small_vwf.source
    sep #0x20
    lda #0xEF
    sta.l small_vwf.source + 2
    rep #0x20
_own_source:
    rts

_field_cells:
"""c1.field: the characters before the FF at [$5E], FE counted: the cells the engine's loop covers."""
    sep #0x20
    rep #0x10
    ldy.w #0x0000
_count:
    lda [0x5E], y
    cmp #0xFF
    beq _counted
    iny
    cpy.w #32
    bcc _count
_counted:
    rep #0x20
    tya
    sta.l c1.field
    rts

_item_icon:
"""An item's record starts with its icon: draw it as a cell, then the name past it. c1.index: 1 for an icon."""
    rep #0x30
    lda.w #0x0000
    sta.l c1.index
    lda.l c1.type
    cmp.w #3
    bne _no_icon
    lda.b 0x5E
    cmp.w #C1_BUFFER & 0xFFFF
    bne _no_icon
    phx
    lda.l small_vwf.source
    tax
    lda.l C1_ITEM_RECORDS & 0xFF0000, x
    and.w #0x00FF
    tax
    lda.l C1_TILE_MAP, x
    and.w #0x00FF
    ora.w #C1_ATTR
    plx
    sta.l C1_SHADOW, x
    inx
    inx
    lda.l small_vwf.source
    inc
    sta.l small_vwf.source
    lda.l c1.field
    dec
    sta.l c1.field
    lda.w #0x0001
    sta.l c1.index
_no_icon:
    sep #0x20
    rts

_draw_cells:
"""Write the field's cells from X: slots for the rendered ones, blanks after; X ends past them."""
    rep #0x30
    lda.w #0x0000
    sta.l c1.rows  ; the field's cell
_cell:
    lda.l c1.rows
    cmp.l c1.field
    bcs _drawn
    txa
    sta.l c1.cell
    sep #0x20
    lda.l c1.rows
    cmp.l small_vwf.cells
    rep #0x20
    bcs _blank
    phx
    jsr.w _slot_for_cell
    plx
    bcs _put
_blank:
    lda.w #C1_BLANK_TILE
_put:
    ora.w #C1_ATTR
    sta.l C1_SHADOW, x
    inx
    inx
    lda.l c1.rows
    inc
    sta.l c1.rows
    bra _cell
_drawn:
    rts

_slot_for_cell:
"""A slot for c1.cell, filled with rendered cell c1.rows: A = its tile, carry set; clear when none."""
    lda.l c1.cell
    inc
    sta.l c1.key
    ldx.w #( C1_SLOTS - 1 ) * 2
_own:
    lda.l c1.slot_owner, x
    cmp.l c1.key
    beq _found
    dex
    dex
    bpl _own
    ldx.w #0x0000
_free:
    lda.l c1.slot_owner, x
    beq _found
    phx
    dec
    tax
    lda.l C1_SHADOW, x
    and.w #0x03FF
    sta.l c1.slot
    plx
    txa
    lsr
    jsr.w _slot_tile
    cmp.l c1.slot
    bne _found  ; its cell shows something else
    inx
    inx
    cpx.w #C1_SLOTS * 2
    bcc _free
    clc
    rts
_found:
    lda.l c1.key
    sta.l c1.slot_owner, x
    txa
    lsr
    sta.l c1.slot
    jsr.w _fill_slot
    lda.l c1.slot
    jsr.w _slot_tile
    sec
    rts

_slot_tile:
"""Slot A (16-bit) -> its tile (16-bit A). Keeps X."""
    cmp.w #C1_KANA_SLOTS
    bcs _blank_tiles
    clc
    adc.w #0x33
    rts
_blank_tiles:
    cmp.w #C1_KANA_SLOTS + C1_BLANK_SLOTS
    bcs _hidden_tiles
    clc
    adc.w #0x170 - C1_KANA_SLOTS
    rts
_hidden_tiles:
    clc
    adc.w #0x100 - C1_KANA_SLOTS - C1_BLANK_SLOTS
    rts

_fill_slot:
"""Slot c1.slot draws rendered cell c1.rows as a 4bpp tile; its run goes dirty when the tile changes."""
    lda.l c1.slot
    asl
    asl
    asl
    asl
    asl
    tax  ; X: the slot's tile
    lda.l c1.rows
    asl
    asl
    asl
    asl
    tay  ; Y: the rendered cell
    sep #0x20
    lda #0x00
    sta.l c1.changed
    rep #0x20
_fill_row:
    phx
    tyx
    lda.l small_vwf.tiles, x  ; a row's planes 0 and 1
    plx
    cmp.l c1.tiles, x
    beq _row_same
    sta.l c1.tiles, x
    pha
    sep #0x20
    lda #0x01
    sta.l c1.changed
    rep #0x20
    pla
_row_same:
    sep #0x20
    sta.l c1.plane  ; plane 0
    xba
    ora.l c1.plane  ; | plane 1
    eor #0xFF
    sta.l c1.tiles + C1_TILE_2BPP, x  ; plane 2: the background
    lda #0x00
    sta.l c1.tiles + C1_TILE_2BPP + 1, x
    rep #0x20
    inx
    inx
    iny
    iny
    tya
    and.w #C1_TILE_2BPP - 1
    bne _fill_row
    sep #0x20
    lda.l c1.changed
    beq _unchanged
    lda.l c1.slot
    cmp #C1_KANA_SLOTS
    lda #0x01
    bcc _run_bit
    lda.l c1.slot
    cmp #C1_KANA_SLOTS + C1_BLANK_SLOTS
    lda #0x02
    bcc _run_bit
    lda #0x04
_run_bit:
    ora.l c1.dirty
    sta.l c1.dirty
_unchanged:
    rep #0x30
    rts

c1_upload:
"""
Upload the dirty runs on channel 0 (the callback sets its own transfer after), then sep #0x20 / lsr $3C as the
callback began.
"""
    php
    sep #0x20
    lda.l c1.dirty
    beq _clean
    rep #0x30
    phx
    phy
    lda.w #0x0000
    tax
_upload_run:
    sep #0x20
    lda.l _run_bits, x
    beq _uploaded
    and.l c1.dirty
    rep #0x20
    beq _next_upload
    lda #0x1801
    sta.l 0x004300
    lda.l _run_vram, x
    sta.l 0x002116
    lda.l _run_source, x
    sta.l 0x004302
    lda.l _run_bytes, x
    sta.l 0x004305
    sep #0x20
    lda #c1.tiles >> 16
    sta.l 0x004304
    lda #0x80
    sta.l 0x002115
    lda #0x01
    sta.l 0x00420B
_next_upload:
    rep #0x20
    inx
    inx
    bra _upload_run
_uploaded:
    sep #0x20
    lda #0x00
    sta.l c1.dirty
    rep #0x30
    ply
    plx
_clean:
    plp
    sep #0x20
    lsr.b 0x3C
    rtl

_record_tables:
; By type * 2: record 0 of the names C12EC0 copies (bank EF); characters have none here.
    .dw 0x0000
    .dw 0x1F50  ; enemies
    .dw 0x5920  ; spells
    .dw 0x3CA0  ; items, 9 bytes a record
    .dw 0x63D8  ; dragons
_run_bits:
    .db 0x01, 0x00, 0x02, 0x00, 0x04, 0x00, 0x00
_run_vram:
    .dw C1_FONT_VRAM + 0x33 * 16
    .dw C1_FONT_VRAM + 0x170 * 16
    .dw C1_FONT_VRAM + 0x100 * 16
_run_source:
    .dw c1.tiles & 0xFFFF
    .dw ( c1.tiles + C1_KANA_SLOTS * C1_TILE_4BPP ) & 0xFFFF
    .dw ( c1.tiles + ( C1_KANA_SLOTS + C1_BLANK_SLOTS ) * C1_TILE_4BPP ) & 0xFFFF
_run_bytes:
    .dw C1_KANA_SLOTS * C1_TILE_4BPP
    .dw C1_BLANK_SLOTS * C1_TILE_4BPP
    .dw ( C1_SLOTS - C1_KANA_SLOTS - C1_BLANK_SLOTS ) * C1_TILE_4BPP
}
