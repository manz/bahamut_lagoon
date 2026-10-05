"""
Variable-width text for the 4bpp text buffer at 7E7800: the load screen chapter titles and the messages table.

Both vanilla loops draw 12px glyphs from the original font in bank ED, which the patch overwrote. They now hand
the string to draw_string, which renders vwf.bin glyphs the way the game shades its own: plane 1 is the glyph,
plane 0 the glyph and its shadow (one pixel right and down), so colour 3 on colour 1.
"""


.include "src/expansion.i"

.import "vwf_font"

TEXT_BUFFER = 0x7800  ; bank 7E: top tile row, bottom row 0x200 after it, columns 16-31 0x400 after that
TEXT_BUFFER_SIZE = 0x800
GLYPH_HEIGHT = 16  ; vwf.bin: 16 rows of 1bpp, then the advance width
WRMPYA = 0x4202
WRMPYB = 0x4203
RDMPY = 0x4216
DMA_QUEUE_TAIL = 0x001A00  ; next free 8-byte entry of the game's DMA queue, drained in NMI (EE41DB)
MESSAGE_TILES = 0x7C00  ; VRAM word of the message window tiles
MESSAGE_SPRITES = 0x7E6E20  ; OAM shadow of the message sprites: x, y, tile, attribute
MESSAGE_SPRITES_MAX = 15  ; 16px each from x 0x18, so the last stays left of x 256

; Direct-page scratch: the words both vanilla 12px loops use as scratch themselves. $12-$16 (index and string
; pointer) are the caller's and stay untouched.
_position = 0x00  ; pen x, in pixels (word)
_delta = 0x18  ; buffer distance from this column to the next (word)
_low_halves = 0x1A  ; scratch (word)
_multiplier = 0x1C  ; 0x80 >> (pen x & 7): multiplying by it then doubling shifts a glyph row into place (byte)
_shadow = 0x1D  ; previous glyph row, which shades this one from above (byte)
_rows = 0x1E  ; rows left in the glyph (byte)
_glyph_row = 0x1F  ; (byte)

.alloc text_buffer_vwf in expansion {
draw_string:
"""
Clear the text buffer and draw [$14] from index $12 to its FF terminator, from x = 0. Codes F0-F3 select a font
page of the 12px font and are skipped. Clobbers $00-$01 and $18-$1F.
"""


    php
    phb
    rep #0x30
    pea 0x7E7E
    plb
    plb

    ldx.w #TEXT_BUFFER_SIZE - 2
_clear:
    stz.w TEXT_BUFFER, x
    dex
    dex
    bpl _clear

    stz _position
    ldy 0x12
_next_char:
    lda [0x14], y
    and.w #0x00FF
    cmp.w #0x00FF
    beq _done
    cmp.w #0x00F0
    bcs _skip
    phy
    jsr.w draw_char
    ply
_skip:
    iny
    bra _next_char
_done:
; Leave $12 and $1C as the vanilla loop does: the index of the terminator, and the buffer address of the
; last column drawn.
    sty 0x12
    lda _position
    beq _empty
    dec
    lsr
    lsr
    lsr
    jsr.w column_offset
_empty:
    clc
    adc.w #TEXT_BUFFER
    sta 0x1C
    plb
    plp
    rtl

draw_message:
"""
draw_string for the messages table, then queue the buffer for the message window tiles. The vanilla loop uploads
each glyph from its char routine (EE515C), which no longer runs.
"""


    jsr.l draw_string
    php
    rep #0x30
    lda.w #0x000
    ldy.w #MESSAGE_TILES
    jsr.w queue_upload
    lda.w #0x200
    ldy.w #MESSAGE_TILES + 0x100
    jsr.w queue_upload
    lda.w #0x400
    ldy.w #MESSAGE_TILES + 0x200
    jsr.w queue_upload
    lda.w #0x600
    ldy.w #MESSAGE_TILES + 0x300
    jsr.w queue_upload
    jsr.w place_message_sprites
    plp
    rtl

place_message_sprites:
"""
Show one 16px sprite per 16 pixels drawn. The vanilla char routine (EE532D) counts them by chars and steps back 8px
after the 7th, since a 12px message only fills 120px of each 128px tile row; the VWF fills them, so no step.
"""


    lda _position
    clc
    adc.w #15
    lsr
    lsr
    lsr
    lsr
    beq _no_sprites
    cmp.w #MESSAGE_SPRITES_MAX
    bcc _count
    lda.w #MESSAGE_SPRITES_MAX
_count:
    tay
    lda.w #0xC818  ; y 0xC8, x 0x18
    ldx 0x32
    cpx.w #0x275
    bne _place
    lda.w #0xC014  ; message 0x275 sits higher, as in EE532D
_place:
    ldx.w #0
_sprite:
    sta.l MESSAGE_SPRITES, x
    clc
    adc.w #0x10
    inx
    inx
    inx
    inx
    dey
    bne _sprite
_no_sprites:
    rts

queue_upload:
"""Queue 0x200 bytes of the text buffer from offset A to VRAM word Y, as EE515C and EE55BB build their entries."""
    pha
    lda.l DMA_QUEUE_TAIL
    tax
    lda.w #0x8000
    sta.l 0x000006, x
    tya
    sta.l 0x000003, x
    lda.w #0x0200
    sta.l 0x000005, x
    lda.w #0x7E00
    sta.l 0x000001, x
    pla
    clc
    adc.w #TEXT_BUFFER
    sta.l 0x000000, x
    txa
    clc
    adc.w #8
    sta.l DMA_QUEUE_TAIL
    rts

draw_char:
"""Draw the glyph of char A (16-bit) at the pen and advance it. Expects DB 7E and 16-bit registers."""
    sta _low_halves
    asl
    asl
    asl
    asl
    clc
    adc _low_halves
    tax  ; X: the glyph, 17 bytes per char

    lda _position
    lsr
    lsr
    lsr
    pha
    jsr.w column_offset
    tay  ; Y: top row of the pen's column
    pla
    inc
    jsr.w column_offset
    sty _delta
    sec
    sbc _delta
    sta _delta

    lda _position
    and.w #0x0007
    phx
    tax
    sep #0x20
    lda.l _multipliers, x
    plx
    sta _multiplier
    stz _shadow
    lda #GLYPH_HEIGHT
    sta _rows

_row:
    sep #0x20
    lda.l assets_vwf_bin, x
    sta _glyph_row
    jsr.w shifted  ; plane 1: the glyph
    pha
    sep #0x20
    lda _glyph_row
    lsr
    ora _glyph_row
    ora _shadow
    jsr.w shifted  ; plane 0: the glyph and its shadow
    sta _low_halves
    sep #0x20
    lda _glyph_row
    sta _shadow  ; shades the next row
    rep #0x20

; This column takes the high halves, the next one the low halves; plane 0 is the even byte of each row.
    lda _low_halves
    and.w #0x00FF
    pha
    lda 3, s
    xba
    and.w #0xFF00
    ora 1, s
    sta 1, s  ; next column's word
    lda 3, s
    and.w #0xFF00
    sta 3, s
    lda _low_halves
    xba
    and.w #0x00FF
    ora 3, s  ; this column's word
    ora.w TEXT_BUFFER, y
    sta.w TEXT_BUFFER, y
    tya
    clc
    adc _delta
    tay
    pla
    ora.w TEXT_BUFFER, y
    sta.w TEXT_BUFFER, y
    tya
    sec
    sbc _delta
    tay
    pla

    inx
    iny
    iny
    sep #0x20
    dec _rows
    beq _advance
    lda _rows
    cmp #GLYPH_HEIGHT / 2
    bne _row
    rep #0x20
    tya
    clc
    adc.w #0x200 - 0x10  ; rows 8-15 go to the bottom tile row
    tay
    bra _row

_advance:
    rep #0x20
    lda.l assets_vwf_bin, x  ; the advance width follows the rows
    and.w #0x00FF
    sec  ; and one pixel of spacing
    adc _position
    sta _position
    rts

shifted:
"""A (8-bit) shifted right by pen x & 7, as a 16-bit value with the spill in the low byte. Returns 16-bit A."""
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

column_offset:
"""Buffer offset of the top row of column A (16-bit)."""
    pha
    and.w #0x000F
    asl
    asl
    asl
    asl
    asl
    sta _low_halves
    pla
    and.w #0x0010
    asl
    asl
    asl
    asl
    asl
    asl
    clc
    adc _low_halves
    rts

_multipliers:
    .db 0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01
}

; The load screen chapter title loop (EE554B) and the messages loop (EE5409): draw the whole string, then rejoin
; the vanilla code after the loop.
.alloc at 0xEE554B {
    jsr.l draw_string
    jmp.w 0x55BB
}
.alloc at 0xEE5409 {
    jsr.l draw_message
    jmp.w 0x5484
}
