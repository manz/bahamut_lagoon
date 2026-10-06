"""
The battle engine's text through small_vwf: every string the C0 engine copies into a line of the unit panel or a
window (the command window, the spell and skill lists).

The engine composes a line in a buffer (LINE, direct page; D = 0x0100), copying each string with panel_copy_string
(C0E089: bank $10, string Y, $08 cells, at X), then draws it a cell at a time (panel_draw_line, then panel_put_char)
with the line's attribute in $10. Attribute 0x22 is the unit panel on BG3: tile 0x200 + code, the 2bpp font at
0x4000. Attribute 0x23 is a BG1 window (the command window, the message box): tile 0x300 + code, a 4bpp font the
engine loads at 0x3000 only while such a window is up, over the map's own tiles.

A copy of three characters or more renders (two-letter labels like LV keep the font): its cells take PLACEHOLDER,
the tiles wait in a line strip and the characters in a line copy. Drawn, a placeholder takes the slot its tilemap row
and cell had, or a free one, from the panel's slots or the windows'; a row's slots its last drawing left unused are
freed when the row is drawn again. Changed pixels mark the slot's run of codes dirty and the battle NMI uploads dirty
runs whole, a transfer each: slot by slot, the bookkeeping alone outlasts vblank. Window slots keep a 4bpp copy (the
glyph over the window background, colour 4) for the window font; their runs go up one an NMI, and only once a window
line changed them or the window font came back, so never over the map tiles the window font replaces.

The panel slots are 8x8 font codes no text draws once the battle text is French: the kana (below 0x33 the engine
draws a kana with a dakuten mark instead, and 0x33-0x5F are the kana themselves), around the frame tiles (0x10,
0x1A) and the colour fills (0x2D-0x2F) the battle uses. The window slots are the window font's kana.
"""

.include "src/expansion.i"
.include "src/sram_work.i"
.include "src/tile_pool.i"
.extern small_vwf_render
.extern small_vwf
.extern tile_blit
.extern tile_pool


LINE = 0x0620
LINE_CELLS = 30
COPY_CELLS = 12  ; small_vwf's cells: a longer field is blank past them
MAX_CHARS = 24  ; small_vwf's
BOX_MARGIN = 2  ; cells a map message box adds past its text: a blank and the prompt arrow
PLACEHOLDER = 0x01
BLANK = 0xEF
TILE_BYTES = 16
FONT_VRAM = 0x4000  ; BG3 tile 0x200, 8x8 code 0x00
PANEL_ATTR = 0x22
POOL_SLOTS = 75  ; the panel's, then the windows'
WINDOW_SLOTS = 45
ALL_SLOTS = POOL_SLOTS + WINDOW_SLOTS
WINDOW_VRAM = 0x3000  ; BG1 tile 0x300, 8x8 code 0x00, 4bpp
WINDOW_TILE_BYTES = 32
MIN_CHARS = 3  ; shorter copies (LV, HP) keep the font
SLOT_STALE = 0x01  ; not drawn since its row was last drawn
ALL_RUNS = 0x0F  ; the panel's
WINDOW_RUNS = 0x70
FIRST_WINDOW_RUN = 4 * 2

; line_strip, line_chars, line_cells: the line being composed (a field may render past it), its characters (BLANK
; past them) and where small_vwf drew. pool_owner: tilemap row + 1 holding the slot, 0 when free. pool_cell: the line
; cell the slot draws. pool_flags: SLOT_STALE. window_tiles: the window slots in 4bpp. dirty: a bit per run of
; _pool_runs to upload. first, last: the slot range a placeholder takes from. slot_run: run * 2. source,
; window_source: the upload's sources. copy_end: Y as the engine's copy leaves it.
.struct PanelVwf {
    byte[( LINE_CELLS + COPY_CELLS ) * TILE_BYTES] line_strip
    byte[LINE_CELLS] line_chars
    byte[LINE_CELLS] line_cells
    byte[ALL_SLOTS * TILE_BYTES] pool_tiles
    word[ALL_SLOTS] pool_owner
    byte[ALL_SLOTS] pool_cell
    byte[ALL_SLOTS] pool_flags
    byte[WINDOW_SLOTS * WINDOW_TILE_BYTES] window_tiles
    byte dirty
    word first
    word last
    word cell
    word row
    word slot
    word slot_run
    byte slot_code
    byte changed
    word source
    word window_source
    word copy_end
}

.reserve panel as PanelVwf in sram_work


; panel_copy_string: phb / lda $10 / pha / plb.
.alloc at 0xC0E089 {
    jml.l panel_copy_hook
    nop
}

; panel_draw_line: sta $10 / phb / lda #0x7E, the tilemap cell in $16.
.alloc at 0xC0DE22 {
    jml.l panel_line_hook
    nop
}

; panel_put_char: cmp #0xEF / bne.
.alloc at 0xC0CADE {
    jml.l panel_put_char_hook
}

; Battle NMI, its transfers done: lda #0x0F / sta $2100 ends the forced blank. Its transfers use addresses the main
; loop sets beforehand, so the runs go up after them.
.alloc at 0xC0F505 {
    jsl.l panel_nmi_upload
    nop
}

; The 8x8 font upload (rep #0x21 / lda.l 0xC70020) writes over the slots.
.alloc at 0xC0B41A {
    jml.l panel_font_reloaded
    nop
    nop
}

; The map's message box copy (C0AB4B: bank A, string Y into the line, its characters in $08, which size the box):
; through panel_copy_string, so the box draws the VWF and fits its cells.
.alloc at 0xC0AB4B {
    sta.b 0x10
    jsl.l panel_count_chars
    ldx.w #LINE
    jsr.w 0xE089
    jsl.l panel_end_box_line
    rts
}

; Its draw loop (C0AB2A: ldx #0 / lda $000720, x) indexes the line from 0; put_char's hook takes X as a line
; position, as panel_draw_line passes it: the same bytes from LINE.
.alloc at 0xC0AB2A {
    ldx.w #LINE
    lda.l 0x000100, x
}

; The window font upload's last transfer (sta $420B / rts) writes over the window slots.
.alloc at 0xC0C537 {
    jml.l panel_window_font_reloaded
}


.alloc battle_panel_vwf in expansion {
panel_copy_hook:
"""
A copy into the line buffer that small_vwf draws in fewer cells renders through it; any other goes on as the
engine wrote it.
"""
    cpx.w #LINE
    bcc _vanilla_copy
    cpx.w #LINE + LINE_CELLS
    bcs _vanilla_copy
    lda #MAX_CHARS  ; the field's cells bound it, not its characters
    sta.l small_vwf.max_chars
    lda.b 0x08
    beq _vanilla_copy
    cmp #COPY_CELLS
    bcc _cells
    lda #COPY_CELLS
_cells:
    sta.l small_vwf.max_cells
    lda.b 0x10
    sta.l small_vwf.source + 2
    rep #0x20
    tya
    sta.l small_vwf.source
    sep #0x20
    jsl.l small_vwf_render
    lda.l small_vwf.chars
    cmp #MIN_CHARS
    bcc _vanilla_copy  ; a short label: the font draws it, the pool stays free
    jsr.w _copy_end
    jsr.w _keep_cells
    jsr.w _fill_cells
    rep #0x20
    lda.l panel.copy_end
    tay
    sep #0x20
    jml.l 0xC0E0A2  ; the copy routine's rts
_vanilla_copy:
    phb
    lda.b 0x10
    pha
    plb
    jml.l 0xC0E08E

_copy_end:
"""Where the engine's copy leaves Y: past $08 bytes, or past the FF before them (FE is a character to it)."""
    phb
    phy
    lda.b 0x10
    pha
    plb
    lda.b 0x08
    sta.l panel.cell
_scan:
    lda.w 0x0000, y
    iny
    cmp #0xFF
    beq _scanned
    lda.l panel.cell
    dec
    sta.l panel.cell
    bne _scan
_scanned:
    rep #0x20
    tya
    sta.l panel.copy_end
    sep #0x20
    ply
    plb
    rts

_keep_cells:
"""Copy the rendered tiles into the line strip at the field's cell (X - LINE)."""
    rep #0x30
    phx
    txa
    sec
    sbc.w #LINE
    asl
    asl
    asl
    asl
    tay  ; Y: strip byte
    ldx.w #0x0000
    sep #0x20
_keep:
    lda.l small_vwf.tiles, x
    phx
    tyx
    sta.l panel.line_strip, x
    plx
    inx
    iny
    cpx.w #COPY_CELLS * TILE_BYTES
    bcc _keep
    plx
    rts

_fill_cells:
"""
Fill the field's $08 cells: a placeholder where small_vwf drew or a character remains, else a blank, then a blank
past the end as the engine leaves it; the line copy keeps each cell's character and whether small_vwf drew it. X ends
on that blank.
"""
    rep #0x20
    lda.w #0x0000
    sta.l panel.cell  ; the field's cell
    sep #0x20
_fill:
    lda.b 0x08
    beq _filled
    dec.b 0x08
    cpx.w #LINE + LINE_CELLS
    bcs _filled
    phx  ; the line position
    rep #0x20
    txa
    sec
    sbc.w #LINE
    tay  ; Y: the line cell
    lda.l panel.cell
    tax  ; X: the field cell
    sep #0x20
    txa
    cmp.l small_vwf.chars
    lda #BLANK
    bcs _char
    lda.l small_vwf.text, x
_char:
    tyx
    sta.l panel.line_chars, x
    xba  ; the character waits in B
    lda.l panel.cell
    cmp.l small_vwf.cells
    lda #0x00
    bcs _drawn_flag
    inc
_drawn_flag:
    sta.l panel.line_cells, x
    bne _placeholder_cell
    xba
    cmp #BLANK
    beq _put
_placeholder_cell:
    lda #PLACEHOLDER
_put:
    plx
    sta.b 0x00, x
    inx
    lda.l panel.cell
    inc
    sta.l panel.cell
    bra _fill
_filled:
    lda #BLANK
    sta.b 0x00, x
    rts

panel_line_hook:
"""The row about to be drawn ($16): free its slots the last drawing left stale, mark the others stale."""
    sta.b 0x10
    rep #0x30
    phx
    lda.b 0x16
    jsr.w _row_owner
    sta.l panel.row
    ldx.w #ALL_SLOTS - 1
_age:
    rep #0x20
    txa
    asl
    phx
    tax
    lda.l panel.pool_owner, x
    plx
    cmp.l panel.row
    bne _other_row
    sep #0x20
    lda.l panel.pool_flags, x
    bne _release
    lda #SLOT_STALE
    sta.l panel.pool_flags, x
    bra _other_row
_release:
    lda #0x00
    sta.l panel.pool_flags, x
    rep #0x20
    txa
    asl
    phx
    tax
    lda.w #0x0000
    sta.l panel.pool_owner, x
    plx
_other_row:
    dex
    bpl _age
    rep #0x30
    plx
    sep #0x20
    phb
    lda #0x7E
    jml.l 0xC0DE27

_row_owner:
"""A: tilemap cell (16-bit) -> its row + 1."""
    lsr
    lsr
    lsr
    lsr
    lsr
    lsr
    inc
    rts

panel_put_char_hook:
"""
A: the character, X: past it in the line, Y: its tilemap cell. On the panel a placeholder becomes a pool tile, in
a window the character it stands for.
"""
    cmp #BLANK
    bne _not_blank
_draw_blank:
    jml.l 0xC0CAE2
_not_blank:
    cmp #PLACEHOLDER
    beq _placeholder
_draw_char:
    jml.l 0xC0CAE9
_placeholder:
    rep #0x30
    phx
    txa
    sec
    sbc.w #LINE + 1
    sta.l panel.cell
    tax
    rep #0x20
    lda.w #0x0000
    sta.l panel.first
    lda.w #POOL_SLOTS
    sta.l panel.last
    sep #0x20
    lda.b 0x10
    cmp #PANEL_ATTR
    beq _panel_cell
    rep #0x20
    lda.w #POOL_SLOTS  ; a window: its own slots
    sta.l panel.first
    lda.w #ALL_SLOTS
    sta.l panel.last
    sep #0x20
_panel_cell:
    lda.l panel.line_cells, x
    bne _drawn
    plx
    lda #BLANK
    bra _draw_blank
_drawn:
    rep #0x20
    tya
    jsr.w _row_owner
    sta.l panel.row
    jsr.w _find_slot
    bcs _slot_found
    plx
    sep #0x20
    lda #BLANK
    bra _draw_blank  ; the pool is full
_slot_found:
    sta.l panel.slot
    jsr.w _slot_code
    sta.l panel.slot_code
    rep #0x20
    txa
    sta.l panel.slot_run
    lda.l panel.slot
    jsr.w _fill_slot
    sep #0x20
    lda.l panel.slot_code
    plx
    jml.l 0xC0CAED

_find_slot:
"""
The slot (16-bit A, carry set) of panel.row's panel.cell in panel.first..last, else a free one taken for it;
carry clear: none.
"""
    lda.l panel.last
    dec
    asl
    tax
_find_own:
    lda.l panel.pool_owner, x
    cmp.l panel.row
    bne _not_own
    phx
    txa
    lsr
    tax
    sep #0x20
    lda.l panel.pool_cell, x
    eor.l panel.cell
    rep #0x20
    plx  ; pulling X sets the flags: test the cell after
    and.w #0x00FF
    beq _have
_not_own:
    jsr.w _slot_before
    bcs _find_own
    lda.l panel.last
    dec
    asl
    tax
_find_free:
    lda.l panel.pool_owner, x
    beq _take
    jsr.w _slot_before
    bcs _find_free
    clc
    rts

_slot_before:
"""X (slot * 2) steps to the slot before; carry clear when it was panel.first."""
    txa
    lsr
    cmp.l panel.first
    beq _past_first
    dex
    dex
    sec
    rts
_past_first:
    clc
    rts
_take:
    lda.l panel.row
    sta.l panel.pool_owner, x
_have:
    txa
    lsr
    sec
    rts

_fill_slot:
"""Slot A (16-bit) draws strip cell panel.cell: fresh again, its run dirty when its pixels change. Keeps Y."""
    tax
    sep #0x20
    lda.l panel.cell
    sta.l panel.pool_cell, x
    lda #0x00
    sta.l panel.pool_flags, x
    rep #0x20
    txa
    asl
    asl
    asl
    asl
    clc
    adc.w #panel.pool_tiles & 0xFFFF
    sta.l tile_pool.destination
    lda.l panel.cell
    asl
    asl
    asl
    asl
    clc
    adc.w #panel.line_strip & 0xFFFF
    sta.l tile_pool.source
    sep #0x20
    lda #panel.line_strip >> 16
    sta.l tile_pool.source + 2
    lda #panel.pool_tiles >> 16
    sta.l tile_pool.destination + 2
    lda #TILE_2BPP
    sta.l tile_pool.format
    jsl.l tile_blit
    lda #0x00
    rol
    sta.l panel.changed
    jsr.w _window_copy  ; even unchanged: a blank cell's window copy still needs its colour 4
    lda.l panel.changed
    beq _unchanged
    rep #0x20
    lda.l panel.slot_run
    tax
    sep #0x20
    lda.l _run_bits, x
    ora.l panel.dirty
    sta.l panel.dirty
_unchanged:
    rep #0x30
    rts

_window_copy:
"""A window slot (panel.slot) gets its 4bpp copy, over the window's colour 4; panel.changed when it changed."""
    rep #0x30
    lda.l panel.slot
    sec
    sbc.w #POOL_SLOTS
    bcc _not_window
    asl
    asl
    asl
    asl
    asl
    clc
    adc.w #panel.window_tiles & 0xFFFF
    sta.l tile_pool.destination
    lda.l panel.slot
    asl
    asl
    asl
    asl
    clc
    adc.w #panel.pool_tiles & 0xFFFF
    sta.l tile_pool.source
    sep #0x20
    lda #panel.pool_tiles >> 16
    sta.l tile_pool.source + 2
    lda #panel.window_tiles >> 16
    sta.l tile_pool.destination + 2
    lda #TILE_4BPP_FILL
    sta.l tile_pool.format
    jsl.l tile_blit
    lda #0x00
    rol
    ora.l panel.changed
    sta.l panel.changed
_not_window:
    sep #0x20
    rts

_slot_code:
"""A: slot (16-bit) -> its 8x8 code (8-bit A), X: its run * 2."""
    ldx.w #0x0000
    sep #0x20
_run:
    cmp.l _pool_runs + 1, x
    bcc _in_run
    sec
    sbc.l _pool_runs + 1, x
    inx
    inx
    bra _run
_in_run:
    clc
    adc.l _pool_runs, x
    rts

panel_nmi_upload:
"""Upload the dirty runs, then end the forced blank as the NMI did (lda #0x0F / sta $2100)."""
    php
    sep #0x20
    lda.l panel.dirty
    beq _clean
    jsr.w _upload_runs
_clean:
    sep #0x20
    lda #0x0F
    sta.l 0x002100
    plp
    rtl

_upload_runs:
"""DMA each dirty run on channel 0 to the panel font, keeping the channel's registers."""
    rep #0x30
    pha
    phx
    phy
    sep #0x20
    ldx.w #0x0006
_save:
    lda.l 0x004300, x
    pha
    dex
    bpl _save
    lda #0x80  ; word writes, the address stepping after the high byte, as the engine's uploads leave it
    sta.l 0x002115
    lda #0x01
    sta.l 0x004300
    lda #0x18
    sta.l 0x004301
    lda #panel.pool_tiles >> 16
    sta.l 0x004304
    rep #0x20
    lda.w #panel.pool_tiles & 0xFFFF
    sta.l panel.source
    ldx.w #0x0000
_run_upload:
    lda.l _pool_runs, x
    and.w #0x00FF
    beq _uploaded
    cpx.w #FIRST_WINDOW_RUN
    bcs _window_run
    lda.l _pool_runs + 1, x
    and.w #0x00FF
    asl
    asl
    asl
    asl
    tay  ; Y: the run's bytes
    sep #0x20
    lda.l _run_bits, x
    and.l panel.dirty
    rep #0x20
    beq _next_run
    lda.l _pool_runs, x
    and.w #0x00FF
    asl
    asl
    asl
    clc
    adc.w #FONT_VRAM
    jsr.w _transfer
_next_run:
    tya
    clc
    adc.l panel.source
    sta.l panel.source
    inx
    inx
    bra _run_upload
_window_run:
    jsr.w _upload_window_run
_uploaded:
    sep #0x20
    lda.l panel.dirty
    and #WINDOW_RUNS  ; the window runs left for the next NMIs
    sta.l panel.dirty
    ldx.w #0x0000
_restore:
    pla
    sta.l 0x004300, x
    inx
    cpx.w #0x0007
    bcc _restore
    rep #0x30
    ply
    plx
    pla
    rts

_transfer:
"""DMA Y bytes from panel.source to VRAM word A on channel 0 (16-bit A)."""
    sta.l 0x002116
    lda.l panel.source
    sta.l 0x004302
    tya
    sta.l 0x004305
    sep #0x20
    lda #0x01
    sta.l 0x00420B
    rep #0x20
    rts

_upload_window_run:
"""The first dirty window run from X on, if any: its 4bpp tiles to the window font; its bit cleared."""
    lda.w #panel.window_tiles & 0xFFFF
    sta.l panel.window_source
_window_upload:
    lda.l _pool_runs, x
    and.w #0x00FF
    beq _window_done
    lda.l _pool_runs + 1, x
    and.w #0x00FF
    asl
    asl
    asl
    asl
    asl
    tay  ; Y: the run's bytes
    sep #0x20
    lda.l _run_bits, x
    and.l panel.dirty
    rep #0x20
    beq _next_window_run
    sep #0x20
    lda.l _run_bits, x
    eor #0xFF
    and.l panel.dirty
    sta.l panel.dirty
    rep #0x20
    lda.l panel.window_source
    sta.l panel.source
    lda.l _pool_runs, x
    and.w #0x00FF
    asl
    asl
    asl
    asl
    clc
    adc.w #WINDOW_VRAM
    jmp.w _transfer  ; one window run an NMI
_next_window_run:
    tya
    clc
    adc.l panel.window_source
    sta.l panel.window_source
    inx
    inx
    bra _window_upload
_window_done:
    rts

panel_count_chars:
"""$08: the characters of string Y in bank $10 before its FF, counted as C0AB4B did (F0-F3 switch font pages)."""
    phb
    phy
    lda.b 0x10
    pha
    plb
    stz.b 0x08
_count_char:
    lda.w 0x0000, y
    iny
    cmp #0xFF
    beq _counted
    cmp #0xF4
    bcs _counts
    cmp #0xF0
    bcs _count_char
_counts:
    inc.b 0x08
    bra _count_char
_counted:
    ply
    plb
    rtl

panel_end_box_line:
"""
End the line after the cells the copy drew and leave their count, plus BOX_MARGIN, in $08: small_vwf's when it
rendered the string, else the characters up to the first blank.
"""
    rep #0x10
    lda.l small_vwf.chars
    cmp #MIN_CHARS
    bcc _font_cells
    lda.l small_vwf.cells
    rep #0x20
    and.w #0x00FF
    clc
    adc.w #LINE
    tax
    sep #0x20
    bra _box_end
_font_cells:
    ldx.w #LINE
_box_cell:
    lda.b 0x00, x
    cmp #BLANK
    beq _box_end
    cmp #0xFF
    beq _box_end
    inx
    cpx.w #LINE + LINE_CELLS
    bcc _box_cell
_box_end:
    lda #0xFF
    sta.b 0x00, x
    rep #0x20
    txa
    sec
    sbc.w #LINE - BOX_MARGIN  ; and room before the box's prompt arrow, which sits in the last cell
    sep #0x20
    sta.b 0x08
    rtl

panel_window_font_reloaded:
"""The window font upload overwrites the window slots: upload them again, one run an NMI."""
    sta.l 0x00420B
    php
    sep #0x20
    lda.l panel.dirty
    ora #WINDOW_RUNS
    sta.l panel.dirty
    plp
    jml.l 0xC006E1  ; an rts in the engine's bank: back to the window font's caller

panel_font_reloaded:
"""The font upload overwrites the slots: upload them all again at the next NMI."""
    php
    sep #0x20
    lda #ALL_RUNS
    sta.l panel.dirty
    plp
    rep #0x21
    lda.l 0xC70020
    jml.l 0xC0B420

_pool_runs:
; The pool's runs of free codes, slot after slot: first code, length; 0 ends them.
    .db 0x0D, 3
    .db 0x11, 9
    .db 0x1B, 18
    .db 0x33, 45
    .db 0x33, 15  ; the windows'
    .db 0x42, 15
    .db 0x51, 15
    .db 0x00
_run_bits:
; A run's bit in panel.dirty, by run * 2.
    .db 0x01, 0x00, 0x02, 0x00, 0x04, 0x00, 0x08, 0x00, 0x10, 0x00, 0x20, 0x00, 0x40, 0x00
}
