"""
The menu engine's fixed-cell names through small_vwf.

draw_fixed_name (EE4D1F: bank A, string Y, X - 1 characters at most) writes one tilemap cell a character into the
shadow at 7EC400 + text_cursor ($1860), tile = code | attribute ($1862). The shadow's first 0x1000 bytes are BG3
over the 2bpp menu font at VRAM 0x4000; the rest is BG2 over a 4bpp copy at 0x1000. Item records start with their
icon, drawn as a cell of its own here before the name.

A name longer than its field (a full name past its record) renders through small_vwf; the others fit and stay in
the font. On BG2 its cells take a run of slots from VRAM 0x2000-0x2FFF, blank in the menus (BG2 tiles 0x100-0x1FF).
BG3 cannot reach below its 0x4000 base: its cells take first the last rows of its own 32x64 map, 58-63, which no
menu scrolls to (the boxes at the bottom scroll it by 224 and 241 lines, down to row 57): BG3 tiles 0x1E8-0x1FF,
whose pixels go into the shadow there, for the engine's upload of the shadow to carry. Then font codes no French
text draws: blank ones (0x15-0x1F) and the kana (0x33-0x5F). A name that cannot have all its cells stays in the
font, cut at its record.

A slot belongs to a shadow cell and is free again once that cell shows something else. The tiles wait in a staging
buffer for the engine's DMA queue ($1A02 on, the tail in $1A00, drained whole in its NMI, which
resets the tail). The queue has no bound and no drain while a screen is being set up, so entries stay few: a BG2
run that continues the last entry, in VRAM and in the staging buffer, grows it instead of adding one (runs are taken
in order, so a screen's names mostly make one). The staging buffer starts over once the queue has drained.
"""

.include "src/expansion.i"
.include "src/sram_work.i"
.extern small_vwf_render
.extern small_vwf


MENU_TEXT_CURSOR = 0x001860
MENU_TEXT_ATTR = 0x001862
MENU_SHADOW = 0x7EC400
MENU_BG2_CELLS = 0x1000  ; shadow offsets from here are BG2
MENU_DMA_QUEUE_TAIL = 0x001A00
MENU_BLANK = 0xEF
MENU_TILE_2BPP = 16
MENU_TILE_4BPP = 32
MENU_ITEM_RECORDS = 0xEF3CA0
MENU_ITEM_RECORD = 9
MENU_ITEMS = 128
MENU_BG2_SLOTS = 256
MENU_BG2_TILE = 0x100  ; BG2 tile of slot 0
MENU_BG2_VRAM = 0x2000
MENU_BG3_MAP_SLOTS = 24  ; map rows 58-63, from MENU_BG3_MAP_TILE
MENU_BG3_MAP_TILE = 0x1E8
MENU_BG3_MAP_PIXELS = 0xE80  ; shadow offset of tile MENU_BG3_MAP_TILE's pixels: row 58
MENU_BG3_SLOTS = MENU_BG3_MAP_SLOTS + 56
MENU_BG3_BLANK_CODES = 11  ; 0x15-0x1F, then the kana from 0x33
MENU_BG3_VRAM = 0x4000
MENU_STAGING_TILES = 160  ; 4bpp tiles a drain can carry
MENU_MAX_CELLS = 12  ; small_vwf's

; bg2_owner, bg3_owner: the shadow cell a slot draws, plus 1; 0 when free (cells are even). bg2_next: where the next
; run search starts. staged: staging bytes waiting for the drain. entry, entry_source: the last queue entry and the
; staging address it carries, to tell a drain. field: the cells the engine's draw covers. The rest is scratch.
.struct MenuVwf {
    byte[MENU_STAGING_TILES * MENU_TILE_4BPP] staging
    word[MENU_BG2_SLOTS] bg2_owner
    word[MENU_BG3_SLOTS] bg3_owner
    word bg2_next
    word staged
    word entry
    word entry_source
    word field
    word cell
    word slot
    word index
    word count
    word tries
    word tile
}

.reserve menu as MenuVwf in sram_menu


; draw_fixed_name: php / phb / phx / sep #0x20.
.alloc at 0xEE4D1F {
    jml.l menu_draw_fixed_name
}


.alloc menu_vwf in expansion {
menu_draw_fixed_name:
"""A (low byte): bank, Y: string, X: characters + 1. Renders through small_vwf when the name overflows its field."""
    php
    rep #0x30
    pha
    phx
    phy
    sep #0x20
    sta.l small_vwf.source + 2
    rep #0x20
    tya
    sta.l small_vwf.source
    txa
    dec
    sta.l menu.field
    jsr.w _item_icon
    jsr.w _field_cells
    sep #0x20
    lda.l menu.field
    beq _vanilla
    sta.l small_vwf.max_chars
    cmp #MENU_MAX_CELLS + 1
    bcc _cells
    lda #MENU_MAX_CELLS
_cells:
    sta.l small_vwf.max_cells
    jsl.l small_vwf_render
    lda.l menu.field
    cmp.l small_vwf.chars
    bcs _vanilla  ; it fits: the font draws it
    jsr.w _drain_check
    jsr.w _free_field
    lda.l MENU_TEXT_CURSOR
    cmp.w #MENU_BG2_CELLS
    bcc _bg3
    jsr.w _draw_bg2
    bra _done
_bg3:
    jsr.w _draw_bg3
_done:
    rep #0x30
    ply
    plx
    pla
    plp
    rtl
_vanilla:
    rep #0x30
    ply
    plx
    pla
    lda.l small_vwf.source  ; past the icon, if any
    tay
    lda.l menu.field
    inc
    tax
    sep #0x20
    lda.l small_vwf.source + 2
    plp
    php
    phb
    phx
    sep #0x20
    jml.l 0xEE4D24

_item_icon:
"""An item record (MENU_ITEM_RECORDS + id * 9): draw its icon as a cell and move the string and field past it."""
    sep #0x20
    lda.l small_vwf.source + 2
    cmp #MENU_ITEM_RECORDS >> 16
    bne _no_icon
    rep #0x20
    lda.l small_vwf.source
    sec
    sbc.w #MENU_ITEM_RECORDS & 0xFFFF
    bcc _no_icon
    cmp.w #MENU_ITEMS * MENU_ITEM_RECORD
    bcs _no_icon
    sta.l 0x004204
    sep #0x20
    lda #MENU_ITEM_RECORD
    sta.l 0x004206
    rep #0x20
    nop  ; the remainder is ready 16 cycles on
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    lda.l 0x004216
    bne _no_icon
    lda.l small_vwf.source
    tax
    lda.l MENU_ITEM_RECORDS & 0xFF0000, x
    and.w #0x00FF
    ora.l MENU_TEXT_ATTR
    pha
    lda.l MENU_TEXT_CURSOR
    tax
    pla
    sta.l MENU_SHADOW, x
    txa
    inc
    inc
    sta.l MENU_TEXT_CURSOR
    lda.l small_vwf.source
    inc
    sta.l small_vwf.source
    lda.l menu.field
    dec
    sta.l menu.field
_no_icon:
    rep #0x30
    rts

_field_cells:
"""menu.field: the cells the engine's loop covers, up to menu.field characters or the FF before (FE counts)."""
    phb
    sep #0x20
    lda.l small_vwf.source + 2
    pha
    plb
    rep #0x30
    lda.l small_vwf.source
    tay
    lda.l menu.field
    tax
    lda.w #0x0000
    sta.l menu.cell
_count:
    txa
    beq _counted
    sep #0x20
    lda.w 0x0000, y
    cmp #0xFF
    rep #0x20
    beq _counted
    lda.l menu.cell
    inc
    sta.l menu.cell
    iny
    dex
    bra _count
_counted:
    lda.l menu.cell
    sta.l menu.field
    plb
    rts

_drain_check:
"""Start the staging buffer over once the queue no longer holds the last entry."""
    rep #0x30
    lda.l menu.entry
    beq _drained
    cmp.l MENU_DMA_QUEUE_TAIL
    bcs _drained
    tax
    lda.l 0x000000, x
    cmp.l menu.entry_source
    beq _pending
_drained:
    lda.w #0x0000
    sta.l menu.staged
    sta.l menu.entry
_pending:
    rts

_free_field:
"""Free the BG2 slots the field's cells show: they are about to be drawn over."""
    rep #0x30
    lda.w #0x0000
    sta.l menu.index
_free_cell:
    lda.l menu.index
    cmp.l menu.field
    bcs _freed
    asl
    clc
    adc.l MENU_TEXT_CURSOR
    tax
    lda.l MENU_SHADOW, x
    and.w #0x03FF
    sec
    sbc.w #MENU_BG2_TILE
    cmp.w #MENU_BG2_SLOTS
    bcs _not_bg2
    asl
    tax
    lda.w #0x0000
    sta.l menu.bg2_owner, x
_not_bg2:
    lda.l menu.index
    inc
    sta.l menu.index
    bra _free_cell
_freed:
    rts

_draw_bg2:
"""Take a run of slots for the rendered cells, stage and queue them, write the field's cells."""
    rep #0x30
    lda.l small_vwf.cells
    and.w #0x00FF
    sta.l menu.count
    asl
    asl
    asl
    asl
    asl
    clc
    adc.l menu.staged
    cmp.w #MENU_STAGING_TILES * MENU_TILE_4BPP + 1
    bcs _bg2_full  ; the drain carries no more this frame
    jsr.w _find_run
    bcc _bg2_full
    sta.l menu.slot
    jsr.w _stage_run
    jsr.w _queue_run
    lda.w #0x0000
    sta.l menu.index
_bg2_cell:
    lda.l menu.index
    cmp.l menu.field
    bcs _bg2_drawn
    asl
    clc
    adc.l MENU_TEXT_CURSOR
    tax  ; X: the cell
    lda.l menu.index
    cmp.l menu.count
    bcs _bg2_blank
    clc
    adc.l menu.slot
    pha
    asl
    phx
    tax
    lda 0x01, s  ; the cell
    inc
    sta.l menu.bg2_owner, x
    plx
    pla
    clc
    adc.w #MENU_BG2_TILE
    bra _bg2_put
_bg2_blank:
    lda.w #MENU_BLANK
_bg2_put:
    ora.l MENU_TEXT_ATTR
    sta.l MENU_SHADOW, x
    lda.l menu.index
    inc
    sta.l menu.index
    bra _bg2_cell
_bg2_drawn:
    jmp.w _advance
_bg2_full:
    jmp.w _draw_plain_cells

_find_run:
"""
A run of menu.count free BG2 slots from bg2_next on, not wrapping: its first slot in A, carry set; carry clear
when none.
"""
    lda.l menu.bg2_next
    sta.l menu.slot
    lda.w #MENU_BG2_SLOTS
    sta.l menu.tries
_try_run:
    lda.l menu.slot
    clc
    adc.l menu.count
    cmp.w #MENU_BG2_SLOTS + 1
    bcc _run_fits
    lda.w #0x0000
    sta.l menu.slot
_run_fits:
    lda.w #0x0000
    sta.l menu.index
_check_slot:
    lda.l menu.index
    cmp.l menu.count
    bcs _run_found
    clc
    adc.l menu.slot
    jsr.w _bg2_free
    bcc _taken
    lda.l menu.index
    inc
    sta.l menu.index
    bra _check_slot
_taken:
    lda.l menu.slot
    sec  ; past the taken slot
    adc.l menu.index
    cmp.w #MENU_BG2_SLOTS
    bcc _next_try
    lda.w #0x0000
_next_try:
    sta.l menu.slot
    lda.l menu.tries
    dec
    sta.l menu.tries
    bne _try_run
    clc
    rts
_run_found:
    lda.l menu.slot
    clc
    adc.l menu.count
    cmp.w #MENU_BG2_SLOTS
    bcc _next_start
    lda.w #0x0000
_next_start:
    sta.l menu.bg2_next
    lda.l menu.slot
    sec
    rts

_bg2_free:
"""Slot A (16-bit): carry set when free, or when its cell no longer shows it (then freed)."""
    asl
    tax
    lda.l menu.bg2_owner, x
    beq _is_free
    phx
    dec
    tax
    lda.l MENU_SHADOW, x
    plx
    and.w #0x03FF
    sec
    sbc.w #MENU_BG2_TILE
    asl
    sta.l menu.tile
    txa
    cmp.l menu.tile
    beq _in_use
    lda.w #0x0000
    sta.l menu.bg2_owner, x
_is_free:
    sec
    rts
_in_use:
    clc
    rts

_stage_run:
"""Copy the rendered cells as 4bpp tiles (planes 2 and 3 clear) into the staging buffer at menu.staged."""
    lda.l menu.staged
    tax
    ldy.w #0x0000
    lda.l menu.count
    asl
    asl
    asl
    asl
    sta.l menu.tile  ; 2bpp bytes to copy
_stage:
    tya
    cmp.l menu.tile
    bcs _staged
    phx
    tyx
    lda.l small_vwf.tiles, x  ; a row's planes 0 and 1
    plx
    sta.l menu.staging, x
    lda.w #0x0000
    sta.l menu.staging + MENU_TILE_2BPP, x
    inx
    inx
    iny
    iny
    tya
    and.w #MENU_TILE_2BPP - 1
    bne _stage
    txa
    clc
    adc.w #MENU_TILE_2BPP  ; past the upper planes
    tax
    bra _stage
_staged:
    rts

_queue_run:
"""Queue the staged run for VRAM MENU_BG2_VRAM + slot * 16, as the engine builds its entries (EE515C)."""
    lda.l menu.count
    asl
    asl
    asl
    asl
    asl
    sta.l menu.tile  ; bytes
    lda.l menu.slot
    asl
    asl
    asl
    asl
    clc
    adc.w #MENU_BG2_VRAM
    jsr.w _extend
    bcs _extended
    jmp.w _queue
_extended:
    rts

_extend:
"""
Grow the last entry by menu.tile bytes when it is still the queue's last and the run at VRAM word A continues
it; carry set when it did. The staging buffer moves past the bytes.
"""
    sta.l menu.cell  ; the run's VRAM word
    lda.l menu.entry
    beq _no_extend
    clc
    adc.w #8
    cmp.l MENU_DMA_QUEUE_TAIL
    bne _no_extend  ; another entry came after, or the queue drained
    lda.l menu.entry
    tax
    lda.l 0x000000, x
    cmp.l menu.entry_source
    bne _no_extend
    lda.l 0x000005, x
    clc
    adc.l menu.entry_source
    sec
    sbc.w #menu.staging & 0xFFFF
    cmp.l menu.staged
    bne _no_extend  ; not followed by this run in the staging buffer
    lda.l 0x000005, x
    lsr
    clc
    adc.l 0x000003, x
    cmp.l menu.cell
    bne _no_extend  ; not followed by this run in VRAM
    lda.l 0x000005, x
    clc
    adc.l menu.tile
    sta.l 0x000005, x
    lda.l menu.entry  ; drained meanwhile? then the run goes in an entry of its own
    clc
    adc.w #8
    cmp.l MENU_DMA_QUEUE_TAIL
    bne _no_extend_after
    lda.l menu.staged
    clc
    adc.l menu.tile
    sta.l menu.staged
    sec
    rts
    _no_extend_after:  ; the run's tiles stay where they are staged, for an entry of their own
_no_extend:
    lda.l menu.cell
    clc
    rts

_queue:
"""Queue menu.tile staged bytes for VRAM word A; the staging buffer moves past them."""
    pha
    lda.l MENU_DMA_QUEUE_TAIL
    tax
    sta.l menu.entry
    lda.w #0x8000
    sta.l 0x000006, x
    pla
    sta.l 0x000003, x
    lda.l menu.tile
    sta.l 0x000005, x
    lda.w #( menu.staging >> 8 ) & 0xFF00
    sta.l 0x000001, x
    lda.l menu.staged
    clc
    adc.w #menu.staging & 0xFFFF
    sta.l 0x000000, x
    sta.l menu.entry_source
    txa
    clc
    adc.w #8
    sta.l MENU_DMA_QUEUE_TAIL
    lda.l menu.staged
    clc
    adc.l menu.tile
    sta.l menu.staged
    rts

_draw_bg3:
"""BG3: a slot a rendered cell, filled one by one; blanks after. The font draws the name when slots run short."""
    rep #0x30
    jsr.w _bg3_free_count
    lda.l small_vwf.cells
    and.w #0x00FF
    cmp.l menu.count
    beq _bg3_room_ok
    bcc _bg3_room_ok
    jmp.w _draw_plain_cells
_bg3_room_ok:
    lda.w #0x0000
    sta.l menu.index
_bg3_cell:
    lda.l menu.index
    cmp.l menu.field
    bcs _bg3_drawn
    asl
    clc
    adc.l MENU_TEXT_CURSOR
    sta.l menu.cell
    sep #0x20
    lda.l menu.index
    cmp.l small_vwf.cells
    rep #0x20
    bcs _bg3_blank
    jsr.w _bg3_slot
    bcs _bg3_put
_bg3_blank:
    lda.w #MENU_BLANK
_bg3_put:
    ora.l MENU_TEXT_ATTR
    pha
    lda.l menu.cell
    tax
    pla
    sta.l MENU_SHADOW, x
    lda.l menu.index
    inc
    sta.l menu.index
    bra _bg3_cell
_bg3_drawn:
    jmp.w _advance

_bg3_slot:
"""
A free BG3 slot for menu.cell, filled with rendered cell menu.index: A = its tile, carry set; clear when none.
The map slots come first.
"""
    ldx.w #0x0000
_bg3_find:
    lda.l menu.bg3_owner, x
    beq _bg3_take
    phx
    dec
    tax
    lda.l MENU_SHADOW, x
    and.w #0x03FF
    sta.l menu.tile
    plx
    txa
    lsr
    jsr.w _bg3_code
    cmp.l menu.tile
    bne _bg3_take  ; its cell shows something else
_bg3_next:
    inx
    inx
    cpx.w #MENU_BG3_SLOTS * 2
    bcc _bg3_find
    clc
    rts
_bg3_take:
    cpx.w #MENU_BG3_MAP_SLOTS * 2
    bcc _bg3_room
    lda.l menu.staged  ; a font slot goes through the staging buffer
    clc
    adc.w #MENU_TILE_2BPP
    cmp.w #MENU_STAGING_TILES * MENU_TILE_4BPP + 1
    bcs _bg3_next
_bg3_room:
    lda.l menu.cell
    inc
    sta.l menu.bg3_owner, x
    txa
    lsr
    pha
    cmp.w #MENU_BG3_MAP_SLOTS
    bcs _bg3_font_slot
    jsr.w _map_bg3_cell
    pla
    jsr.w _bg3_code
    sec
    rts
_bg3_font_slot:
    jsr.w _bg3_code
    sta 0x01, s
    jsr.w _stage_bg3_cell
    lda 0x01, s
    asl
    asl
    asl
    clc
    adc.w #MENU_BG3_VRAM
    jsr.w _queue
    pla
    sec
    rts

_map_bg3_cell:
"""Copy rendered cell menu.index into map slot A's pixels in the shadow."""
    asl
    asl
    asl
    asl
    clc
    adc.w #MENU_BG3_MAP_PIXELS
    tax
    lda.l menu.index
    asl
    asl
    asl
    asl
    tay
    lda.w #MENU_TILE_2BPP / 2
    sta.l menu.tile
_map_copy:
    phx
    tyx
    lda.l small_vwf.tiles, x
    plx
    sta.l MENU_SHADOW, x
    inx
    inx
    iny
    iny
    lda.l menu.tile
    dec
    sta.l menu.tile
    bne _map_copy
    rts

_bg3_free_count:
"""
menu.count: the BG3 slots free, or showing nothing any more; font slots only while the staging buffer has
room for them all.
"""
    lda.w #0x0000
    sta.l menu.count
    ldx.w #0x0000
_count_slot:
    lda.l menu.bg3_owner, x
    beq _count_free
    phx
    dec
    tax
    lda.l MENU_SHADOW, x
    and.w #0x03FF
    sta.l menu.tile
    plx
    txa
    lsr
    jsr.w _bg3_code
    cmp.l menu.tile
    beq _count_next
_count_free:
    cpx.w #MENU_BG3_MAP_SLOTS * 2
    bcc _count_it
    lda.l menu.staged
    clc
    adc.w #MENU_TILE_2BPP * 12
    cmp.w #MENU_STAGING_TILES * MENU_TILE_4BPP + 1
    bcs _count_next
_count_it:
    lda.l menu.count
    inc
    sta.l menu.count
_count_next:
    inx
    inx
    cpx.w #MENU_BG3_SLOTS * 2
    bcc _count_slot
    rts

_bg3_code:
"""BG3 slot A (16-bit) -> its tile (16-bit A): a map tile, a blank font code or a kana. Keeps X."""
    cmp.w #MENU_BG3_MAP_SLOTS
    bcs _font_code
    clc
    adc.w #MENU_BG3_MAP_TILE
    rts
_font_code:
    sec
    sbc.w #MENU_BG3_MAP_SLOTS
    cmp.w #MENU_BG3_BLANK_CODES
    bcs _kana
    clc
    adc.w #0x15
    rts
_kana:
    clc
    adc.w #0x33 - MENU_BG3_BLANK_CODES
    rts

_stage_bg3_cell:
"""Stage rendered cell menu.index as a 2bpp tile at menu.staged; menu.tile its bytes."""
    lda.l menu.staged
    tax
    lda.l menu.index
    asl
    asl
    asl
    asl
    tay
    lda.w #MENU_TILE_2BPP
    sta.l menu.tile
_stage3:
    phx
    tyx
    lda.l small_vwf.tiles, x
    plx
    sta.l menu.staging, x
    inx
    inx
    iny
    iny
    tya
    and.w #MENU_TILE_2BPP - 1
    bne _stage3
    rts

_draw_plain_cells:
"""No room for a run: the field's characters in the font, blanks past the string's end."""
    rep #0x30
    lda.w #0x0000
    sta.l menu.index
    sta.l menu.tile  ; nonzero past the end
_plain:
    lda.l menu.index
    cmp.l menu.field
    bcs _advance
    tax
    lda.l small_vwf.text, x
    and.w #0x00FF
    cmp.w #0x00FF
    bne _plain_char
    sta.l menu.tile
_plain_char:
    lda.l menu.tile
    beq _plain_put
    lda.w #MENU_BLANK
    bra _plain_attr
_plain_put:
    lda.l small_vwf.text, x
    and.w #0x00FF
_plain_attr:
    ora.l MENU_TEXT_ATTR
    pha
    lda.l menu.index
    asl
    clc
    adc.l MENU_TEXT_CURSOR
    tax
    pla
    sta.l MENU_SHADOW, x
    lda.l menu.index
    inc
    sta.l menu.index
    bra _plain
_advance:
    rep #0x20
    lda.l menu.field
    asl
    clc
    adc.l MENU_TEXT_CURSOR
    sta.l MENU_TEXT_CURSOR
    rts
}
