"""
Variable-width text for the 4bpp text buffer at 7E7800: the load screen chapter titles and the messages table.

Both vanilla loops draw 12px glyphs from the original font in bank ED, which the patch overwrote. They now hand
the string to draw_string, which renders vwf.bin glyphs the way the game shades its own: plane 0 is the glyph
and its shadow (one pixel right and down), plane 1 the shadow alone, so the letter in colour 1 over a colour 3
shadow.
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
TASK_YIELD = 0xEE440B  ; the game's cooperative task switch
MESSAGE_SPRITES = 0x7E6E20  ; OAM shadow of the message sprites: x, y, tile, attribute
MESSAGE_AT_ONCE = 0x275  ; drawn without a frame between glyphs: the Dragon screen's stat labels
MESSAGE_PEN = 0xF5  ; then the pen's pixel: lays a message out in columns
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

    jsr.w clear_buffer
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
    plb
    plp
    rtl

clear_buffer:
"""Zero the text buffer and put the pen back at x = 0. Expects DB 7E and 16-bit registers."""
    ldx.w #TEXT_BUFFER_SIZE - 2
_clear:
    stz.w TEXT_BUFFER, x
    dex
    dex
    bpl _clear
    stz _position
    rts

draw_message:
"""
Type a message of the messages table, like the vanilla loop: one glyph a frame, each uploaded to the message window
tiles and shown by growing the message sprites, the work its char routine (EE515C, EE532D) did. Message 0x275
appears at once, as in vanilla, its whole buffer queued as one upload: a glyph's four would overrun the DMA queue
into the sound driver's variables at 1D00. MESSAGE_PEN, then a byte, moves the pen to that pixel.
"""


    php
    phb
    rep #0x30
    pea 0x7E7E
    plb
    plb
    jsr.w clear_buffer
    ldy 0x12
_next_glyph:
    lda [0x14], y
    and.w #0x00FF
    cmp.w #0x00FF
    beq _typed
    cmp.w #MESSAGE_PEN
    beq _pen
    cmp.w #0x00F0
    bcs _no_glyph
    phy
    pha
    jsr.w wait_for_uploads
    lda _position
    lsr
    lsr
    lsr
    tay  ; the pen's column: the glyph touches it and the next one
    pla
    phy
    jsr.w draw_char
    pla
    jsr.w queue_glyph
    jsr.w place_message_sprites
    jsr.w yield
    ply
_no_glyph:
    iny
    bra _next_glyph
_pen:
    iny
    lda [0x14], y
    and.w #0x00FF
    sta _position
    iny
    bra _next_glyph
_typed:
    lda 0x32
    cmp.w #MESSAGE_AT_ONCE
    bne _queued
    lda.w #0x0000  ; the whole buffer: the window's tiles follow its layout
    ldx.w #TEXT_BUFFER_SIZE
    jsr.w queue_upload
_queued:
    plb
    plp
    rtl

queue_glyph:
"""Queue the two columns a glyph touches, A and the next; MESSAGE_AT_ONCE goes up whole once typed."""
    pha
    lda 0x32
    cmp.w #MESSAGE_AT_ONCE
    beq _later
    lda 0x01, s
    jsr.w queue_column
    pla
    inc
    jmp.w queue_column
_later:
    pla
    rts

wait_for_uploads:
"""Yield until the game has drained the uploads already queued (00182E clear), as EE515C does."""
    lda 0x32
    cmp.w #MESSAGE_AT_ONCE
    beq _drained
_busy:
    lda.l 0x00182E
    beq _drained
    jsr.l TASK_YIELD
    bra _busy
_drained:
    rts

yield:
"""Let a frame pass between glyphs, as the vanilla loop does, except for message 0x275."""
    lda 0x32
    cmp.w #MESSAGE_AT_ONCE
    beq _no_yield
    jsr.l TASK_YIELD
_no_yield:
    rts

queue_column:
"""Queue the upload of column A (top and bottom tile) to the message window tiles."""
    jsr.w column_offset
    pha
    jsr.w queue_tile
    pla
    clc
    adc.w #0x200
    jmp.w queue_tile

queue_tile:
"""Queue one tile at text buffer offset A for VRAM word MESSAGE_TILES + A / 2."""
    ldx.w #0x0020
queue_upload:
"""
Queue X bytes from text buffer offset A for VRAM word MESSAGE_TILES + A / 2, through the game's DMA queue, building
the entry as EE515C does.
"""
    phx
    pha
    lsr
    clc
    adc.w #MESSAGE_TILES
    tay
    lda.l DMA_QUEUE_TAIL
    tax
    lda.w #0x8000
    sta.l 0x000006, x
    tya
    sta.l 0x000003, x
    lda 0x03, s  ; the byte count
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
    plx
    rts

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
    cpx.w #MESSAGE_AT_ONCE
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
    lsr
    ora _shadow  ; the shadow: one pixel right of this row, and the row above
    pha
    lda _glyph_row
    eor #0xFF
    and 1, s
    jsr.w shifted  ; plane 1: the shadow where the glyph isn't
    sta _low_halves
    sep #0x20
    pla
    ora _glyph_row
    jsr.w shifted  ; plane 0: the glyph and its shadow
    pei (_low_halves)
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
    lda.l vwf_font, x  ; the advance width follows the rows
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

vwf_shift_multipliers:
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
