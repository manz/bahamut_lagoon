"""
Battle unit panel names through small_vwf.

The C0 engine composes each panel line in a buffer (LINE, direct page; D = 0x0100), then draws it one tilemap cell
a character (panel_put_char, C0CADE: tile 0x200 + code on BG3). A name gets six cells. The hooks render the name
and leave placeholder codes in its cells; at draw time panel_put_char swaps each placeholder for a tile of that
panel row, whose pixels go to VRAM with the panel's tilemap upload (C0E38D).

The tiles reuse 8x8 font codes no text draws (below 0x33 the engine draws kana with a dakuten mark instead):
0x11-0x19 and 0x1B-0x29, around 0x10 and 0x1A, which the panel frame uses.
"""

.include "src/expansion.i"
.include "src/sram_work.i"
.extern small_vwf_render
.extern small_vwf
.extern small_vwf_tiles


LINE = 0x0620
NAME_CELLS = 6
NAME_CHARS = 8
PANEL_ROWS = 4
PLACEHOLDER = 0x0D  ; codes PLACEHOLDER .. PLACEHOLDER + NAME_CELLS - 1 stand for the name's cells
BLANK = 0xEF
TILE_BYTES = 16
BLOCK_A_CODE = 0x11  ; slots 0-8
BLOCK_A_SLOTS = 9
BLOCK_B_CODE = 0x1B  ; slots 9-23
BLOCK_B_SLOTS = 15
FONT_VRAM = 0x4000  ; BG3 tile 0x200, 8x8 code 0x00

.reserve panel_name_strip NAME_CELLS * TILE_BYTES in sram_work  ; the line being composed
.reserve panel_name_tiles PANEL_ROWS * NAME_CELLS * TILE_BYTES in sram_work  ; one slot run per panel row


; Names of the units from 9 on: EF0380 + id * 8 (Y). Everything after tay jumps here.
.alloc at 0xC0E07E {
    jml.l panel_name_ef
}

; Names of the first units: 7E2B00 + id * 8 (Y).
.alloc at 0xC0E063 {
    jml.l panel_name_7e
}

; panel_put_char: cmp #0xEF / bne.
.alloc at 0xC0CADE {
    jml.l panel_put_char_hook
}

; Panel tilemap upload: jsr wait_vblank / ldx #0xC000.
.alloc at 0xC0E38D {
    jsl.l panel_upload_tiles
    nop
    nop
}


.alloc battle_panel_vwf in expansion {
panel_name_ef:
    lda #0xEF
    bra _panel_name
panel_name_7e:
    lda #0x7E
_panel_name:
"""Render the name at A:Y into the line's six cells; the copy routine's rts (C0E0A2) returns from there."""
    sta.l small_vwf.source + 2
    rep #0x20
    tya
    sta.l small_vwf.source
    sep #0x20
    lda #NAME_CHARS
    sta.l small_vwf.max_chars
    lda #NAME_CELLS
    sta.l small_vwf.max_cells
    jsl.l small_vwf_render
    ldx.w #NAME_CELLS * TILE_BYTES - 1
_keep:
    lda.l small_vwf_tiles, x
    sta.l panel_name_strip, x
    dex
    bpl _keep
    lda.l small_vwf.cells
    sta.l small_vwf.rows  ; placeholders left
    lda #PLACEHOLDER
    sta.l small_vwf.count  ; the next one
    ldx.w #LINE
_cell:
    lda.l small_vwf.rows
    beq _blank
    dec
    sta.l small_vwf.rows
    lda.l small_vwf.count
    inc
    sta.l small_vwf.count
    dec
    bra _put
_blank:
    lda #BLANK
_put:
    sta.b 0x00, x
    inx
    cpx.w #LINE + NAME_CELLS
    bne _cell
    lda #BLANK
    sta.b 0x00, x  ; the space before the class, as the copy routine leaves it
    jml.l 0xC0E0A2

panel_put_char_hook:
"""A: the character, Y: its tilemap cell (the row above holds dakuten marks). Placeholders become row tiles."""
    cmp #BLANK
    bne _not_blank
    jml.l 0xC0CAE2
_not_blank:
    cmp #PLACEHOLDER
    bcc _vanilla
    cmp #PLACEHOLDER + NAME_CELLS
    bcc _placeholder
_vanilla:
    jml.l 0xC0CAE9
_placeholder:
    phx
    sec
    sbc #PLACEHOLDER
    sta.l small_vwf.count  ; the cell
    rep #0x20
    tya
    clc
    adc.w #0x0040
    asl
    xba
    and.w #PANEL_ROWS - 1  ; (cell + 0x40) >> 7: panel lines are two tilemap rows apart
    sta.l small_vwf.glyph
    asl
    adc.l small_vwf.glyph
    asl
    sta.l small_vwf.glyph  ; row * NAME_CELLS
    lda.l small_vwf.count
    and.w #0x00FF
    clc
    adc.l small_vwf.glyph  ; the slot
    pha
    jsr.w _copy_cell
    pla
    sep #0x20
    cmp #BLOCK_A_SLOTS
    bcc _block_a
    adc #BLOCK_B_CODE - BLOCK_A_SLOTS - 1  ; carry set
    bra _tile
_block_a:
    adc #BLOCK_A_CODE  ; carry clear
_tile:
    plx
    jml.l 0xC0CAED

_copy_cell:
"""Copy the strip's cell small_vwf.count into slot A (16-bit A); returns with 16-bit A."""
    asl
    asl
    asl
    asl
    tax
    lda.l small_vwf.count
    and.w #0x00FF
    asl
    asl
    asl
    asl
    phy
    tay
    sep #0x20
    lda #TILE_BYTES
    sta.l small_vwf.rows
_copy:
    phx
    tyx
    lda.l panel_name_strip, x
    plx
    sta.l panel_name_tiles, x
    inx
    iny
    lda.l small_vwf.rows
    dec
    sta.l small_vwf.rows
    bne _copy
    ply
    rep #0x20
    rts

panel_upload_tiles:
"""Wait for vblank, upload the row tiles on channel 0, and set X for the tilemap upload that follows."""
    php
    sep #0x20
_wait_out:
    lda.l 0x004212
    bmi _wait_out
_wait_in:
    lda.l 0x004212
    bpl _wait_in
    lda.l 0x004300
    pha
    lda.l 0x004301
    pha
    lda #0x01
    sta.l 0x004300
    lda #0x18
    sta.l 0x004301
    lda #panel_name_tiles >> 16
    sta.l 0x004304
    rep #0x20
    lda.w #panel_name_tiles & 0xFFFF
    sta.l 0x004302
    lda.w #BLOCK_A_SLOTS * TILE_BYTES
    sta.l 0x004305
    lda.w #FONT_VRAM + BLOCK_A_CODE * 8
    sta.l 0x002116
    sep #0x20
    lda #0x01
    sta.l 0x00420B
    rep #0x20
    lda.w #( panel_name_tiles + BLOCK_A_SLOTS * TILE_BYTES ) & 0xFFFF
    sta.l 0x004302
    lda.w #BLOCK_B_SLOTS * TILE_BYTES
    sta.l 0x004305
    lda.w #FONT_VRAM + BLOCK_B_CODE * 8
    sta.l 0x002116
    sep #0x20
    lda #0x01
    sta.l 0x00420B
    pla
    sta.l 0x004301
    pla
    sta.l 0x004300
    plp
    ldx.w #0xC000
    rtl
}
