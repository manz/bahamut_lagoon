"""
The tiles small_vwf's callers keep in their pools, converted from its 2bpp cells.

Every caller stores the rendered 2bpp cells in the format its layer reads (see src/tile_pool.i): BG3 takes them as
they are, a BG2 menu as 4bpp over colour 0, a window font (battle, C1) as 4bpp over the window's colour 4.
tile_blit writes one tile and tells whether it changed, so a caller uploads only tiles that did.
"""

.include "src/expansion.i"
.include "src/sram_work.i"
.include "src/tile_pool.i"


TILE_ROWS = 8
TILE_UPPER = 16  ; a 4bpp tile's planes 2 and 3, after its planes 0 and 1

; source: a 2bpp tile. destination: where its converted tile goes. format: TILE_*. changed: scratch.
.struct TilePool {
    long source
    long destination
    byte format
    byte changed
}

.reserve tile_pool as TilePool in sram_work

; Locals, in a stack frame used as the direct page.
LOCALS = 8
_source = 1  ; (long)
_destination = 4  ; (long)
_planes = 7  ; a row's planes 0 and 1 (word)

.alloc tile_pool_code in expansion {
tile_blit:
"""
Convert the 2bpp tile at tile_pool.source into tile_pool.destination as tile_pool.format: carry set when any of
its bytes changed. Any register sizes; keeps A, X, Y, DB and D.
"""
    php
    rep #0x30
    pha
    phx
    phy
    phd
    tsc
    sec
    sbc.w #LOCALS
    tcs
    tcd
    lda.l tile_pool.source
    sta _source
    lda.l tile_pool.source + 1
    sta _source + 1
    lda.l tile_pool.destination
    sta _destination
    lda.l tile_pool.destination + 1
    sta _destination + 1
    sep #0x20
    lda #0x00
    sta.l tile_pool.changed
    rep #0x20
    ldy.w #0x0000
_row:
    lda [_source], y
    sta _planes
    jsr.w _put
    lda.l tile_pool.format
    and.w #0x00FF
    beq _next  ; TILE_2BPP: no upper planes
    cmp.w #TILE_4BPP_FILL
    lda.w #0x0000
    bcc _upper  ; TILE_4BPP: clear
    lda _planes
    xba
    ora _planes
    eor.w #0x00FF  ; plane 2: neither plane 0 nor 1
    and.w #0x00FF  ; plane 3 clear
_upper:
    pha
    tya
    clc
    adc.w #TILE_UPPER
    tay
    pla
    jsr.w _put
    tya
    sec
    sbc.w #TILE_UPPER
    tay
_next:
    iny
    iny
    cpy.w #TILE_ROWS * 2
    bcc _row
    tsc
    clc
    adc.w #LOCALS
    tcs
    pld
    sep #0x20
    lda 0x07, s  ; the caller's P
    and #0xFE
    ora.l tile_pool.changed
    sta 0x07, s
    rep #0x30
    ply
    plx
    pla
    plp
    rtl

_put:
"""Word A at [_destination], y, noting a change."""
    cmp [_destination], y
    beq _kept
    sta [_destination], y
    sep #0x20
    lda #0x01
    sta.l tile_pool.changed
    rep #0x20
_kept:
    rts
}
