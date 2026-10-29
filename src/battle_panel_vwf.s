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
glyph over the window background, colour 4) for the window font; their dirty runs all go up at the next NMI, with
the tilemap that shows them, and only once a window line changed them or the window font came back, so never over the
map tiles the window font replaces.

The panel slots are 8x8 font codes no text draws once the battle text is French: dakuten kana (the engine draws a
kana with a mark instead) from 0x24 up to the colour fills (0x2C-0x2F), and lowercase letters and accents past 0x6B,
which only the VWF draws now. The battle message VWF (battle_vwf_reloc) draws its lines over 0x30 on: its first
line, 0x30-0x6B, shows with the panel; its others overwrite the slots while the dialogue hides the panel, so the
panel uploads its slots again when it next draws a line. A spell list's rows, a name, its level and its MP each, take
that first line's codes too while no battle message draws: one that does frees them. The window slots are the window
font's kana. A sky map
loads its clouds over the font's codes 0x01-0x23 and tiles BG3 with them: no slot sits there.
"""

.include "src/expansion.i"
.include "src/checks.i"
.include "src/sram_work.i"
.include "src/tile_pool.i"
.include "src/vblank.i"
.extern small_vwf_render
.extern small_vwf
.extern tile_blit
.extern tile_pool
.extern dma_fits_vblank
.extern await_vblank


LINE = 0x0620
LINE_CELLS = 30
COPY_CELLS = 12  ; small_vwf's cells: a longer field is blank past them
MAX_CHARS = 24  ; small_vwf's
PARTY_NAMES = 0x2B00  ; bank 7E: the party's names, 8 codes each, FF-terminated only when shorter
PARTY_NAMES_END = PARTY_NAMES + 10 * PARTY_NAME_CODES
PARTY_NAME_CODES = 8
MESSAGE_SPELL_COPY = 0xD6E5  ; the return addresses, less one, of the copies that write a battle message's
MESSAGE_DRAGON_COPY = 0xA7A4  ; name: a spell's, a dragon's
SKILL_LIST_COPY = 0xD6AF  ; the Coup fatal list's call to the spell copy's helper (C0D6D0), less one: a panel line
MESSAGE_RANGE = 0xD5  ; the range icon's first half: a spell message's $10 for its range
SPELL_LIST_ICON = 0xD6B2  ; the spell list row's call for its level icon (jsr C0D6EB), less one: a panel line
NAME_CELLS = 9  ; a list row's name field, the engine's 8 and the cell before the level icon: 72 pixels
ROW_CELLS = 14  ; a spell list row, drawn a tile left of vanilla's: its name, level and MP, up to where its MP ended
ROW_INDENT = 2  ; pixels before the name: room for the cursor
ROW_EDGE = ROW_CELLS * 8 - 2  ; the pixel column its MP ends at: room for the right column's cursor
ROW_CHARS = 28  ; small_vwf's
ROW_NAME_CHARS = 17  ; a row's name, then its level and MP: Lancer de lancier, the widest spell name, whole
ROW_TAB = 0xFB  ; small_vwf's: the rest right-aligned against the column that follows
LETTER_N = 0xC6
LETTER_V = 0x75
DIGIT_ZERO = 0xAF  ; then 1 to 9
LIST_CURSOR_LEFT = 0xFF  ; a spell list's cursor X, 5 pixels left of vanilla's (0x04, 0x7C), 3 pixels before the
LIST_CURSOR_RIGHT = 0x77  ; text: -1, its sign in the high table
CURSOR_LARGE = 0x80  ; a sprite's high table bits as C0:5300 takes them: large, then large with X's sign
CURSOR_LARGE_X9 = 0xC0
OAM_LAST = 0x01FC  ; C0:5300: no sprite past it
BOX_MARGIN = 2  ; cells a map message box adds past its text: a blank and the prompt arrow
PLACEHOLDER = 0x01
BLANK = 0xEF
TILE_BYTES = 16
FONT_VRAM = 0x4000  ; BG3 tile 0x200, 8x8 code 0x00
PANEL_ATTR = 0x22
WINDOW_ATTR = 0x23  ; a BG1 window's line
FRAME_FIRST = 0xE0  ; a window's or the panel's corner, edge and side codes
FRAME_LAST = 0xE2
POOL_SLOTS = 53  ; the panel's, then a spell list's, then the windows'
LIST_SLOTS = 60
WINDOW_FIRST = POOL_SLOTS + LIST_SLOTS
WINDOW_SLOTS = 45
ALL_SLOTS = WINDOW_FIRST + WINDOW_SLOTS
WINDOW_VRAM = 0x3000  ; BG1 tile 0x300, 8x8 code 0x00, 4bpp
WINDOW_TILE_BYTES = 32
SKILL_MENU = 0x64  ; $B0 for a unit's skill window (Terrain's spell kinds, Coup fatal...)
SKILL_CELLS = 8  ; its names' field: Magie blanche, 59 pixels, took 6 cells
SKILL_FRAME_CELLS = 9  ; its frame's inner cells, the engine's 8 and one left of them
FRAME_ROW_BYTES = 0x40  ; a window tilemap row
SKILL_CURSOR_SHIFT = 15  ; pixels its cursor moves left with the names, clear of the frame
SKILL_TEXT = 0x44  ; the first name from the frame's corner: a row down, two cells in (the engine's three)
ROSTER_NAME_CELLS = 7
ROSTER_CLASS_CELLS = 7
DRAGON_KIND_CELLS = 9
MIN_CHARS = 3  ; shorter copies (LV, HP) keep the font
SLOT_STALE = 0x01  ; not drawn since its row was last drawn
ALL_RUNS = 0x03  ; the panel's
LIST_RUN = 0x04
WINDOW_RUNS = 0x38
FIRST_WINDOW_RUN = 3 * 2
UPLOAD_BUDGET = 0x400  ; bytes of runs an NMI uploads: a window's tilemap must still go up in vblank
WINDOW_TILEMAP = 0x7E4000  ; C0AA9E's upload: a window's tilemap
WINDOW_TILEMAP_VRAM = 0x4800
WINDOW_TILEMAP_BYTES = 0x0800
WINDOW_TILEMAP_WAITS = 2  ; vblanks it waits for room at most, then goes up anyway as vanilla
PANEL_TILEMAP = 0x7EC000  ; C0E38D's upload: the panel's BG3 tilemap, after the main loop draws its lines
PANEL_TILEMAP_VRAM = 0x5C00
PANEL_TILEMAP_BYTES = 0x0800
PANEL_TILEMAP_WAITS = 4  ; vblanks it waits for its slots to fit with it at most, then goes up alone as vanilla

; line_strip, line_chars, line_cells: the line being composed (a field may render past it), its characters (BLANK past
; them) and where small_vwf drew. pool_owner: tilemap row + 1 holding the slot, 0 when free. pool_cell: the tilemap
; column the slot draws (a row can show two lines: the Coup fatal list's two skills). pool_flags: SLOT_STALE.
; window_tiles: the window slots in 4bpp. dirty: a bit per run of _pool_runs to upload. first, last: the slot range a
; placeholder takes from. slot_run: run * 2. source, window_source: the upload's sources. copy_end: Y as the engine's
; copy leaves it. message_end: the line position past the last battle message's name. hint: slot * 2 _find_slot tries
; first. first_index, last_index: first and last as slot * 2. line_row, kept: the row whose line is being drawn and the
; slots it kept. column: the placeholder's tilemap column. cursor_x9: nonzero while a spell list's left cursor, past
; the screen's left edge, is being built. list_name: the copy is a spell list row's name. row_text, row_end: that
; row's string, the name's end in it. list_row: the next line drawn is a spell list row; line_list: the one being
; drawn is, and takes the list's slots too; list_slots: nonzero while a list may hold them. number, place, started:
; _put_number's scratch. budget: the bytes of runs an upload may send.
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
    word message_end
    word hint
    word first_index
    word last_index
    word line_row
    word kept
    byte column
    byte cursor_x9
    byte list_name
    byte[ROW_CHARS + 1] row_text
    word row_end
    byte list_row
    byte line_list
    byte list_slots
    byte number
    byte place
    byte started
    word budget
}

.reserve panel as PanelVwf in sram_work
.reserve panel_slots_overwritten 1 in sram_work  ; set by the battle message VWF past its first line
.reserve panel_hold 1 in sram_work  ; nonzero: the next NMI holds the panel's runs back, for a window's tilemap


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

; A window's tilemap, sent by the main loop right after an NMI (four windows' setups): ldx #0x4000 / stx $4302 / ...
.alloc at 0xC0AA9E {
    jsl.l panel_window_tilemap
    rts
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

; A spell in a battle message (C0D6D0: its name; then, from C0D6E7 or C0D6EB, its level or range at the first blank
; of the line's first eight cells: F3 78 F0, Lv in the 12px font, or D5, its range icon, then the number). The name
; is whole and may hold spaces, so the icon goes past it, as the dialogue font spells it. A spell list's row (C0D680)
; is a panel line: D5 is the 8x8 font's Lv, at the first blank past the name's cells, as vanilla; the name takes
; NAME_CELLS there.
.alloc at 0xC0D6F5 {
    jsl.l panel_message_icon
    jml 0xC0D717
}

; A spell list's rows (C0D680) start a tile left, over the blank before each column's cursor, which moves there too
; (C0EA94): the MP goes a cell further along the line, where it was on screen, and the name and level take the cell.
.alloc at 0xC0D6B6 {
    jsl.l panel_list_row  ; was ldy $1C / sty $16
}

.alloc at 0xC0EA96 {
    jsl.l panel_list_cursor  ; was lda #0x04 / sta $0800, y
    nop
}

.alloc at 0xC0EAA1 {
    lda.b #LIST_CURSOR_RIGHT
}

.alloc at 0xC0EB0E {
    jsl.l panel_cursor_bits  ; was lda #0x80 / jsr C0:5300
    nop
}

; The map's message box copy (C0AB4B: bank A, string Y into the line, its characters in $08, which size the box):
; through panel_copy_string, so the box draws the VWF and fits its cells.
.alloc at 0xC0AB4B {
    sta.b 0x10
    jsl.l panel_count_chars
    ldx.w #LINE
    jsr 0xE089
    jsl.l panel_end_box_line
    rts
}

; Its draw loop (C0AB2A: ldx #0 / lda $000720, x) indexes the line from 0; put_char's hook takes X as a line
; position, as panel_draw_line passes it: the same bytes from LINE.
.alloc at 0xC0AB2A {
    ldx.w #LINE
    lda.l 0x000100, x
}

; The unit roster's rows (C0DDDF): the name took 6 cells, the class 8 from the 7th; the class goes a cell right in 7
; (the widest, Garde royal, fits) so a name takes 7, Fils de Zora among them. Its status icons (C0DF87) still start
; at the 7th, past a 7-cell name.
.alloc at 0xC0E068 {
    .db ROSTER_NAME_CELLS  ; a party name (lda #0x06 / sta $08)
}

.alloc at 0xC0E07F {
    .db ROSTER_NAME_CELLS  ; a fixed name (lda #0x06)
}

.alloc at 0xC0E036 {
    .dw LINE + ROSTER_NAME_CELLS + 1  ; the class (ldx #0x0627 / lda #0x08)
    .db 0xA9, ROSTER_CLASS_CELLS
}

; A dragon's line in the unit panel (C0DC1F): its kind in parentheses took 8 cells; Guerrier d'argile needs 9 (68
; pixels), or the closing parenthesis, set past the field's last non-blank cell, covers its last letter.
.alloc at 0xC0DC3D {
    .db DRAGON_KIND_CELLS  ; lda #0x08
}

; The panel's tilemap upload (C0E38D: jsr 06D7, its DMA, rts): its slots first, in the same vblank.
.alloc at 0xC0E38D {
    jml.l panel_bg3_tilemap
}

; A unit's skill window (C0E1CC, its frame; C0E0B2, its names): a tile wider on the left, the names a tile further
; left in the blank the cursor left them, 8 cells where they took 6. Its right edge is the screen's.
.alloc at 0xC0E1CC {
    jml.l panel_skill_frame  ; was phy / phb / lda #0x7E
}

.alloc at 0xC0E0B4 {
    jsl.l panel_skill_text  ; was tya / adc #0x0046 / sta $16
    nop
    nop
}

.alloc at 0xC0E0D1 {
    .db SKILL_CELLS  ; lda #0x06, a skill's name
}

.alloc at 0xC0EACC {
    jsl.l panel_skill_cursor  ; was lda $B7 / sta $0800, y
    nop
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
    lda.b 0x10
    cmp #0x7E
    bne _not_a_party_name
    cpy.w #PARTY_NAMES
    bcc _not_a_party_name
    cpy.w #PARTY_NAMES_END
    bcs _not_a_party_name
    lda #PARTY_NAME_CODES  ; an 8-letter name has no FF: the next name follows
    sta.l small_vwf.max_chars
_not_a_party_name:
    jsr.w _widen_a_list_row
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
    jsr.w _keep_list_name
    jsr.w _for_a_message
    bcc _for_a_line
    jmp.w _message_copy
_for_a_line:
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
    jml 0xC0E0A2  ; the copy routine's rts
_vanilla_copy:
    phb
    lda.b 0x10
    pha
    plb
    jml 0xC0E08E

_widen_a_list_row:
"""A list row's name (the copy helper called from C0D6AD) takes NAME_CELLS, not the engine's 8."""
    rep #0x20
    lda 0x03, s  ; past this jsr: the engine caller's return address, less one
    cmp.w #MESSAGE_SPELL_COPY
    bne _not_a_list_row
    lda 0x05, s
    cmp.w #SKILL_LIST_COPY
    bne _not_a_list_row
    sep #0x20
    lda #NAME_CELLS
    sta.b 0x08
    lda #0x01
    sta.l panel.list_name
_not_a_list_row:
    sep #0x20
    rts

_keep_list_name:
"""A spell list row's name, which small_vwf just resolved: its codes to panel.row_text, ROW_NAME_CHARS at most."""
    lda.l panel.list_name
    beq _list_name_kept
    lda #0x00
    sta.l panel.list_name
    phx
    ldx.w #0x0000
_name_char:
    lda.l small_vwf.text, x
    cmp #0xFF
    beq _name_end
    sta.l panel.row_text, x
    inx
    cpx.w #ROW_NAME_CHARS
    bcc _name_char
_name_end:
    rep #0x20
    txa
    sta.l panel.row_end
    sep #0x20
    plx
_list_name_kept:
    rts

_for_a_message:
"""Carry set when the copy's caller writes a battle message, which the dialogue font draws, not a panel line."""
    rep #0x20
    lda 0x03, s  ; past this jsr: the engine caller's return address, less one
    cmp.w #MESSAGE_SPELL_COPY
    beq _spell
    cmp.w #MESSAGE_DRAGON_COPY
    beq _message
_line:
    sep #0x20
    clc
    rts
_spell:
    lda 0x05, s  ; the helper's caller: the Coup fatal list draws its skills with it too
    cmp.w #SKILL_LIST_COPY
    beq _line
_message:
    sep #0x20
    sec
    rts

_message_copy:
"""
A battle message's name, which small_vwf just resolved: its full codes, then blanks up to the field's end and one
past them, X on that last one, as the engine's copy pads.
"""
    jsr.w _copy_end
    rep #0x20
    lda.w #0x0000
    sta.l panel.cell
    sep #0x20
_message_char:
    phx
    rep #0x20
    lda.l panel.cell
    tax
    sep #0x20
    lda.l small_vwf.text, x
    plx
    cmp #0xFF
    beq _message_pad
    sta.b 0x00, x
    inx
    lda.l panel.cell
    inc
    sta.l panel.cell
    bra _message_char
_message_pad:
    rep #0x20
    txa
    sta.l panel.message_end
    sep #0x20
_message_blank:
    lda.l panel.cell
    cmp.b 0x08
    bcs _message_end
    lda #BLANK
    sta.b 0x00, x
    inx
    lda.l panel.cell
    inc
    sta.l panel.cell
    bra _message_blank
_message_end:
    lda #BLANK
    sta.b 0x00, x
    rep #0x20
    lda.l panel.copy_end
    tay
    sep #0x20
    jml 0xC0E0A2  ; the copy routine's rts

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
"""
Copy the rendered cells into the line strip at the field's cell (X - LINE): only those small_vwf drew, the ones
_fill_cells marks drawn. Keeps X and DB.
"""
    rep #0x30
    phx
    phb
    txa
    sec
    sbc.w #LINE
    asl
    asl
    asl
    asl
    clc
    adc.w #panel.line_strip & 0xFFFF
    tay  ; Y: the strip at the field
    lda.l small_vwf.cells
    and.w #0x00FF
    beq _kept
    asl
    asl
    asl
    asl
    dec  ; the bytes to move, less one
    ldx.w #small_vwf.tiles & 0xFFFF
    mvn small_vwf >> 16, panel >> 16
_kept:
    plb
    plx
    sep #0x20
    rts

_fill_cells:
"""
Fill the field's $08 cells: a placeholder where small_vwf drew, else a blank (the engine trims those back), then a
blank past the end as the engine leaves it; the line copy keeps each cell's character and whether small_vwf drew it.
X ends on that blank.
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
    txa
    cmp.l small_vwf.cells  ; past the ink, its characters already drawn: blank, so the engine trims it
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
"""
The row about to be drawn ($16): free its slots the last drawing left stale, mark the others stale and count them
(panel.line_row, panel.kept); after a battle message's later lines wrote over the slots, upload them all again.
"""
    sta.b 0x10
    lda.l panel.list_row
    sta.l panel.line_list
    beq _not_a_list_line
    sta.l panel.list_slots
    lda #0x00
    sta.l panel.list_row
_not_a_list_line:
    lda.l panel_slots_overwritten
    beq _slots_kept
    lda #0x00
    sta.l panel_slots_overwritten
    jsl.l panel_list_slots_lost
    lda.l panel.dirty
    ora #ALL_RUNS
    sta.l panel.dirty
    lda.b 0x10
_slots_kept:
    rep #0x30
    phx
    lda.b 0x16
    jsr.w _row_owner
    sta.l panel.row
    sta.l panel.line_row
    lda.w #0x0000
    sta.l panel.kept
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
    rep #0x20
    lda.l panel.kept
    inc
    sta.l panel.kept
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
    jml 0xC0DE27

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
    .if CHECKS {
        jsr.w _check_frame
    }
    cmp #BLANK
    bne _not_blank
_draw_blank:
    jml 0xC0CAE2
_not_blank:
    cmp #PLACEHOLDER
    beq _placeholder
_draw_char:
    jml 0xC0CAE9
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
    lda.l panel.line_list
    beq _not_list
    rep #0x20
    lda.w #WINDOW_FIRST  ; a spell list's row: the list's slots too
    sta.l panel.last
    sep #0x20
_not_list:
    lda.b 0x10
    cmp #PANEL_ATTR
    beq _panel_cell
    rep #0x20
    lda.w #WINDOW_FIRST  ; a window: its own slots
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
    lsr
    sep #0x20
    and #0x1F
    sta.l panel.column
    rep #0x20
    tya
    jsr.w _row_owner
    sta.l panel.row
    jsr.w _find_slot
    bcs _slot_found
    jsr.w _reclaim_slots
    jsr.w _find_slot
    bcs _slot_found
    plx
    sep #0x20
    lda #BLANK
    jml 0xC0CAE2  ; the pool is full: a blank
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
    jml 0xC0CAED

    .if CHECKS {
_check_frame:
"""
CHECKS: stop (CHECK_PANEL_FRAME) when the tilemap cell Y (bank 7E, as put_char writes it) holds a window or panel
frame and A, the character put there, is not one. 8-bit A; A and P kept.
"""
        php
        pha
        sep #0x20
        cmp #FRAME_FIRST
        bcc _not_frame_char
        cmp #FRAME_LAST + 1
        bcc _frame_kept  ; a frame redrawn
_not_frame_char:
        phb
        pea 0x7E7E
        plb
        plb
        lda.w 0x0001, y
        and #0x3F  ; the flips aside
        cmp #PANEL_ATTR
        beq _frame_attr
        cmp #WINDOW_ATTR
        bne _no_frame
_frame_attr:
        lda.w 0x0000, y
        cmp #FRAME_FIRST
        bcc _no_frame
        cmp #FRAME_LAST + 1
        bcs _no_frame
        rep #0x20
        lda.w #CHECK_PANEL_FRAME
        stp
_no_frame:
        plb
_frame_kept:
        pla
        plp
        rts
    }

_find_slot:
"""
The slot (16-bit A, carry set) of panel.row's panel.column in panel.first..last, else a free one taken for it;
carry clear: none. A row's cells take slots downwards in order, so the slot before the last one found is tried first,
for its own and for a free one; a row that kept no slot when its line started owns none for its cells.
"""
    lda.l panel.first
    asl
    sta.l panel.first_index
    lda.l panel.last
    dec
    asl
    sta.l panel.last_index
    lda.l panel.hint
    cmp.l panel.first_index
    bcc _scan_own  ; outside the range: no hint
    tax
    cmp.l panel.last_index
    beq _try_hint
    bcs _scan_own
_try_hint:
    jsr.w _owns
    beq _have
_scan_own:
    lda.l panel.line_row
    cmp.l panel.row
    bne _own_anywhere
    lda.l panel.kept
    beq _own_none
_own_anywhere:
    lda.l panel.last_index
    tax
_find_own:
    lda.l panel.pool_owner, x
    cmp.l panel.row
    bne _not_own
    jsr.w _owns_cell
    beq _have
_not_own:
    dex
    dex
    bmi _own_none
    txa
    cmp.l panel.first_index
    bcs _find_own
_own_none:
    lda.l panel.hint
    cmp.l panel.first_index
    bcc _free_from_last
    cmp.l panel.last_index
    beq _free_from_hint
    bcs _free_from_last
_free_from_hint:
    tax
    jsr.w _free_below
    bcs _take
_free_from_last:
    lda.l panel.last_index
    tax
    jsr.w _free_below
    bcs _take
    rts
_take:
    lda.l panel.row
    sta.l panel.pool_owner, x
_have:
    txa
    dec
    dec
    sta.l panel.hint  ; the next cell's slot, likely
    txa
    lsr
    sec
    rts

_reclaim_slots:
"""
Free the slots of panel.first..last whose cell no longer shows them, held by rows other than panel.row: a window closes
without its rows being drawn again, and its slots stayed theirs. 16-bit A and X on return.
"""
    rep #0x30
    lda.l panel.last
    sta.l panel.slot
_reclaim:
    lda.l panel.slot
    dec
    bmi _reclaimed
    cmp.l panel.first
    bcc _reclaimed
    sta.l panel.slot
    asl
    tax
    lda.l panel.pool_owner, x
    beq _reclaim
    cmp.l panel.row
    beq _reclaim
    dec  ; the row's tilemap address in bank 7E: (row + 1 - 1) * 64
    asl
    asl
    asl
    asl
    asl
    asl
    pha
    lda.l panel.slot
    tax
    lda.l panel.pool_cell, x
    and.w #0x00FF
    asl
    clc
    adc 0x01, s
    sta 0x01, s  ; the cell's
    lda.l panel.slot
    jsr.w _slot_code
    plx
    cmp 0x7E0000, x
    rep #0x20
    beq _reclaim  ; still shown
    lda.l panel.slot
    asl
    tax
    lda.w #0x0000
    sta.l panel.pool_owner, x
    bra _reclaim
_reclaimed:
    rts

_free_below:
"""A free slot from X (slot * 2) down to panel.first: X on it, carry set; carry clear: none."""
    lda.l panel.pool_owner, x
    beq _free_found
    dex
    dex
    bmi _no_free
    txa
    cmp.l panel.first_index
    bcs _free_below
_no_free:
    clc
    rts
_free_found:
    sec
    rts

_owns:
"""Zero (16-bit A) when slot X (slot * 2) is panel.row's panel.column. Keeps X."""
    lda.l panel.pool_owner, x
    cmp.l panel.row
    bne _owned
_owns_cell:
    phx
    txa
    lsr
    tax
    sep #0x20
    lda.l panel.pool_cell, x
    eor.l panel.column
    rep #0x20
    plx  ; pulling X sets the flags: test the cell after
    and.w #0x00FF
_owned:
    rts

_fill_slot:
"""
Slot A (16-bit) draws strip cell panel.cell at panel.column: fresh again, its run dirty when its pixels change. Keeps
Y.
"""
    tax
    sep #0x20
    lda.l panel.column
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
    sbc.w #WINDOW_FIRST
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
"""
DMA the dirty runs on channel 0, keeping the channel's registers: the window runs first, whose tilemap the engine
uploads after this NMI, then the panel's, UPLOAD_BUDGET bytes at most, none while panel_hold. A run past the budget
stays dirty for the next NMI: past it, the engine's own uploads (a window's 2 KB tilemap) would run out of vblank.
"""
    rep #0x20
    lda.w #UPLOAD_BUDGET
    sta.l panel.budget
_upload_dirty:
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
    lda.l panel.budget
    pha  ; 1,s: the bytes left
    ldx.w #FIRST_WINDOW_RUN
    jsr.w _upload_window_run
    sep #0x20
    lda.l panel_hold
    rep #0x20
    bne _uploaded  ; a window's tilemap waits for this vblank: the panel's runs, the next one
    lda.w #panel.pool_tiles & 0xFFFF
    sta.l panel.source
    ldx.w #0x0000
_run_upload:
    cpx.w #FIRST_WINDOW_RUN
    bcs _uploaded
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
    tya
    cmp 0x01, s
    beq _fits
    bcs _next_run  ; over the budget: the next NMI
_fits:
    eor.w #0xFFFF
    sec
    adc 0x01, s
    sta 0x01, s
    jsr.w _run_sent
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
_uploaded:
    pla
    sep #0x20
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

_run_sent:
"""Clear run X's dirty bit (16-bit A kept)."""
    pha
    sep #0x20
    lda.l _run_bits, x
    eor #0xFF
    and.l panel.dirty
    sta.l panel.dirty
    rep #0x20
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
"""
Every dirty window run from X on, within the budget at 3,s: its 4bpp tiles to the window font, in the NMI the
window's tilemap goes up.
"""
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
    tya
    cmp 0x03, s
    beq _window_fits
    bcs _next_window_run  ; over the budget: the next NMI
_window_fits:
    eor.w #0xFFFF
    sec
    adc 0x03, s
    sta 0x03, s
    jsr.w _run_sent
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
    jsr.w _transfer
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

panel_bg3_tilemap:
"""
C0E38D's DMA of the panel's tilemap, in a vblank: the dirty runs first, in the same one. The main loop draws the lines
over lag frames, whose NMIs leave the runs behind: sent alone, the tilemap would show other text in its slots for
frames. When the runs and the tilemap cannot both end in this vblank, the next one, PANEL_TILEMAP_WAITS at most; then
the tilemap alone, as vanilla. Returns through C0E38D's rts.
"""
    php
    rep #0x30
    pea.w PANEL_TILEMAP_WAITS
_panel_tilemap_try:
    jsl.l await_vblank
    jsr.w _dirty_bytes
    beq _panel_tilemap_send
    clc
    adc.w #PANEL_TILEMAP_BYTES
    jsl.l dma_fits_vblank
    bcc _panel_runs_send
    lda 0x01, s
    beq _panel_tilemap_send  ; still no room: the tilemap alone
    dec
    sta 0x01, s
    bra _panel_tilemap_try
_panel_runs_send:
    lda.w #0xFFFF
    sta.l panel.budget
    jsr.w _upload_dirty
_panel_tilemap_send:
    pla
    lda.w #PANEL_TILEMAP & 0xFFFF
    sta.l 0x004302
    lda.w #PANEL_TILEMAP_BYTES
    sta.l 0x004305
    lda.w #PANEL_TILEMAP_VRAM
    sta.l 0x002116
    sep #0x20
    lda #PANEL_TILEMAP >> 16
    sta.l 0x004304
    lda #0x01
    sta.l 0x00420B
    plp
    jml 0xC0E3AC  ; C0E38D's rts

_dirty_bytes:
"""A (16-bit, flags set): the bytes of the dirty runs, the windows' in 4bpp. Keeps X."""
    phx
    lda.w #0x0000
    pha  ; 1,s: the bytes
    ldx.w #0x0000
_dirty_run:
    lda.l _pool_runs, x
    and.w #0x00FF
    beq _dirty_counted
    sep #0x20
    lda.l _run_bits, x
    and.l panel.dirty
    rep #0x20
    beq _next_dirty_run
    lda.l _pool_runs + 1, x
    and.w #0x00FF
    asl
    asl
    asl
    asl
    cpx.w #FIRST_WINDOW_RUN
    bcc _run_bytes
    asl
_run_bytes:
    clc
    adc 0x01, s
    sta 0x01, s
_next_dirty_run:
    inx
    inx
    bra _dirty_run
_dirty_counted:
    pla
    plx
    ora.w #0x0000
    rts

panel_skill_frame:
"""
C0E1CC's window frame at Y, $B6 rows, $0A cells wide ($14: the tilemap bytes from a row's right corner to the next
row's left one): a skill window's starts a tile left, SKILL_FRAME_CELLS wide, and its Y stays so for its names. Goes
on at C0E1E1.
"""
    lda.b 0xB0
    cmp #SKILL_MENU
    bne _engine_frame
    dey
    dey
    jsr.w _frame_start
    lda #SKILL_FRAME_CELLS
    ldx.w #FRAME_ROW_BYTES - ( SKILL_FRAME_CELLS + 2 ) * 2
    bra _frame_width
_engine_frame:
    jsr.w _frame_start
    lda #0x08
    ldx.w #0x002C
_frame_width:
    sta.b 0x0A
    stx.b 0x14
    jml 0xC0E1E1

_frame_start:
"""C0E1CC's start but its width: phy (under this call's return), phb, DB 7E, $14 Y, $10 the window attribute."""
    rep #0x20
    pla
    phy
    phb
    pha
    sep #0x20
    lda #0x7E
    pha
    plb
    sty.b 0x14
    lda #WINDOW_ATTR
    sta.b 0x10
    rts

panel_skill_cursor:
"""A window's cursor X ($B7) into its sprite (0x0800, Y): a skill window's SKILL_CURSOR_SHIFT left, with its names."""
    lda.b 0xB0
    cmp #SKILL_MENU
    bne _engine_cursor
    lda.b 0xB7
    sec
    sbc #SKILL_CURSOR_SHIFT
    bra _cursor_placed
_engine_cursor:
    lda.b 0xB7
_cursor_placed:
    sta 0x0800, y
    rtl

panel_skill_text:
"""C0E0B4's first name ($16): the frame's corner Y, a row down and three cells in, or SKILL_TEXT in a skill window."""
    sep #0x20
    lda.b 0xB0
    cmp #SKILL_MENU
    rep #0x21
    bne _engine_text
    tya
    adc.w #SKILL_TEXT
    bra _text_placed
_engine_text:
    tya
    adc.w #0x0046
_text_placed:
    sta.b 0x16
    rtl

panel_window_tilemap:
"""
C0AA9E's DMA, a window's tilemap to VRAM on channel 0 as the NMI leaves it, sent by the main loop right after an NMI:
it ends in vblank only while that NMI was short. When the rest of the vblank cannot hold it, the next NMI holds the
panel's runs back (panel_hold) and it goes up right after that one. Leaves A 0x01 and X the VRAM address, as C0AA9E.
"""
    php
    rep #0x30
    pea.w WINDOW_TILEMAP_WAITS
_tilemap_try:
    lda.w #WINDOW_TILEMAP_BYTES
    jsl.l dma_fits_vblank
    bcc _tilemap_send
    lda 0x01, s
    beq _tilemap_send  ; still no room: as vanilla
    dec
    sta 0x01, s
    sep #0x20
    lda #0x01
    sta.l panel_hold
    rep #0x20
    jsl.l await_vblank
    bra _tilemap_try
_tilemap_send:
    pla
    lda.w #WINDOW_TILEMAP & 0xFFFF
    sta.l 0x004302
    lda.w #WINDOW_TILEMAP_BYTES
    sta.l 0x004305
    lda.w #WINDOW_TILEMAP_VRAM
    sta.l 0x002116
    sep #0x20
    lda #WINDOW_TILEMAP >> 16
    sta.l 0x004304
    lda #0x01
    sta.l 0x00420B
    lda #0x00
    sta.l panel_hold
    plp
    sep #0x20
    rep #0x10
    lda #0x01
    ldx.w #WINDOW_TILEMAP_VRAM
    rtl

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

panel_message_icon:
"""
Past the name the last message copy wrote: a blank, then Nv. for a level ($10 = F3) or the range icon (D5). A spell
list's row takes its level icon at the first blank of its name field, or past it.
"""
    rep #0x20
    lda 0x04, s  ; past this call: the engine's call for the icon, less one
    cmp.w #SPELL_LIST_ICON
    beq _list_icon
    lda.l panel.message_end
    tax
    sep #0x20
    lda #BLANK
    sta.b 0x00, x
    inx
    lda.b 0x10
    cmp #MESSAGE_RANGE
    beq _range
    lda #0xC6  ; N
    sta.b 0x00, x
    inx
    lda #0x75  ; v
    sta.b 0x00, x
    inx
    lda #0xA4  ; .
    bra _icon_end
_range:
    sta.b 0x00, x  ; the icon's two halves, D5 D6
    inx
    inc
_icon_end:
    sta.b 0x00, x
    inx
    rtl
_list_icon:
    sep #0x20
    ldx.w #LINE
_name_cell:
    lda.b 0x00, x
    cmp #BLANK
    beq _icon_end_list
    inx
    cpx.w #LINE + NAME_CELLS
    bne _name_cell
_icon_end_list:
    lda.b 0x10
    bra _icon_end

panel_list_row:
"""
A spell list row, its name kept (panel.row_text), its level ($19, FF: none) and MP ($1B, 0: none) known: one string
through small_vwf, the name, Nv and the level packed, the MP right-aligned against ROW_EDGE, drawn a tile left of the
row ($16, and Y, as vanilla left them) and from the list's slots too. An empty row (FF first) has neither.
"""
    ldx.w #LINE
    lda.b 0x00, x
    cmp #0xFF
    beq _row_placed
    lda.b 0x08
    pha
    rep #0x20
    lda.l panel.row_end
    tax
    sep #0x20
    lda.b 0x19
    cmp #0xFF
    beq _no_level
    lda #BLANK
    sta.l panel.row_text, x
    inx
    lda #LETTER_N
    sta.l panel.row_text, x
    inx
    lda #LETTER_V
    sta.l panel.row_text, x
    inx
    lda.b 0x19
    jsr.w _put_number
_no_level:
    lda.b 0x1B
    beq _no_mp
    lda #ROW_TAB
    sta.l panel.row_text, x
    inx
    lda #ROW_EDGE
    sta.l panel.row_text, x
    inx
    lda.b 0x1B
    jsr.w _put_number
_no_mp:
    lda #0xFF
    sta.l panel.row_text, x
    jsr.w _render_row
    pla
    sta.b 0x08
    lda #0x01
    sta.l panel.list_row
_row_placed:
    rep #0x20
    lda.b 0x1C
    dec
    dec
    sta.b 0x16
    tay
    sep #0x20
    rtl

_render_row:
"""panel.row_text into the line's first ROW_CELLS cells, FF past them; a cell with no ink stays blank, slotless."""
    lda #panel.row_text >> 16
    sta.l small_vwf.source + 2
    rep #0x20
    lda.w #panel.row_text & 0xFFFF
    sta.l small_vwf.source
    sep #0x20
    lda #ROW_CHARS
    sta.l small_vwf.max_chars
    lda #ROW_CELLS
    sta.l small_vwf.max_cells
    lda #ROW_INDENT
    sta.l small_vwf.indent
    jsl.l small_vwf_render
    ldx.w #LINE
    lda #ROW_CELLS
    sta.b 0x08
    jsr.w _keep_cells
    jsr.w _fill_cells
    lda #0xFF
    sta.b 0x00, x
    ldx.w #0x0000
_ink_cell:
    lda.l panel.line_cells, x
    beq _next_ink_cell
    phx
    rep #0x20
    txa
    asl
    asl
    asl
    asl
    tax
    lda.l panel.line_strip, x
    ora.l panel.line_strip + 2, x
    ora.l panel.line_strip + 4, x
    ora.l panel.line_strip + 6, x
    ora.l panel.line_strip + 8, x
    ora.l panel.line_strip + 10, x
    ora.l panel.line_strip + 12, x
    ora.l panel.line_strip + 14, x
    plx
    cmp.w #0x0000  ; the ink, not X
    sep #0x20
    bne _next_ink_cell
    sta.l panel.line_cells, x  ; A: 0
    phx
    rep #0x20
    txa
    clc
    adc.w #LINE
    tax
    sep #0x20
    lda #BLANK
    sta.b 0x00, x
    plx
_next_ink_cell:
    inx
    cpx.w #ROW_CELLS
    bcc _ink_cell
    rts

_put_number:
"""A (8-bit): its decimal digits at panel.row_text, X on; X past them."""
    sta.l panel.number
    lda #0x00
    sta.l panel.started
    lda #100
    jsr.w _put_digit
    lda #10
    jsr.w _put_digit
    lda #0x01
    sta.l panel.started  ; the units, even 0
_put_digit:
    sta.l panel.place
    ldy.w #0x0000
    lda.l panel.number
_count_place:
    cmp.l panel.place
    bcc _place_counted
    sbc.l panel.place
    iny
    bra _count_place
_place_counted:
    sta.l panel.number
    tya
    ora.l panel.started
    beq _digit_skipped  ; a leading zero
    tya
    clc
    adc #DIGIT_ZERO
    sta.l panel.row_text, x
    inx
    lda #0x01
    sta.l panel.started
_digit_skipped:
    rts

panel_list_slots_lost:
"""
A battle message draws over the list's slots (0x30-0x6B): they are free again, their pixels gone, nothing to upload.
Any register sizes; all registers and P are kept.
"""
    php
    rep #0x30
    pha
    phx
    sep #0x20
    lda.l panel.list_slots
    beq _list_slots_kept
    lda #0x00
    sta.l panel.list_slots
    lda.l panel.dirty
    and #LIST_RUN ^ 0xFF
    sta.l panel.dirty
    rep #0x20
    ldx.w #( WINDOW_FIRST - 1 ) * 2
_free_list_slot:
    lda.w #0x0000
    sta.l panel.pool_owner, x
    dex
    dex
    cpx.w #POOL_SLOTS * 2
    bcs _free_list_slot
_list_slots_kept:
    rep #0x30
    plx
    pla
    plp
    rtl

panel_list_cursor:
"""A spell list's cursor X: a tile left of vanilla's, the left column's past the screen edge (X's sign set)."""
    lda #LIST_CURSOR_LEFT
    sta 0x0800, y
    lda.b 0xC1
    and #0x01
    eor #0x01
    sta.l panel.cursor_x9
    rtl

panel_cursor_bits:
"""
A cursor's high table bits (C0:5300, which a jsl cannot reach): large, with X's sign for a spell list's left cursor.
"""
    lda #CURSOR_LARGE
    xba
    lda.l panel.cursor_x9
    beq _cursor_bits
    lda #0x00
    sta.l panel.cursor_x9
    lda #CURSOR_LARGE_X9
    xba
_cursor_bits:
    xba
    cpy.w #OAM_LAST
    bcc _cursor_room
    dey
    dey
    dey
    dey
    rtl
_cursor_room:
    sty.b 0x12
    sta.b 0x10
    ldy.b 0xE6
    lda 0x0A00, y
    lsr
    lsr
    ora.b 0x10
    sta 0x0A00, y
    dec.b 0xFE
    bne _cursor_counted
    lda #0x04
    sta.b 0xFE
    inc.b 0xE6
_cursor_counted:
    ldy.b 0x12
    rtl

panel_window_font_reloaded:
"""The window font upload overwrites the window slots: upload them again at the next NMI."""
    sta.l 0x00420B
    php
    sep #0x20
    lda.l panel.dirty
    ora #WINDOW_RUNS
    sta.l panel.dirty
    plp
    jml 0xC006E1  ; an rts in the engine's bank: back to the window font's caller

panel_font_reloaded:
"""The font upload overwrites the slots: upload them all again at the next NMI."""
    php
    sep #0x20
    lda.l panel.list_slots
    beq _list_free
    lda #LIST_RUN
_list_free:
    ora #ALL_RUNS
    sta.l panel.dirty
    plp
    rep #0x21
    lda 0xC70020
    jml 0xC0B420

_pool_runs:
; The pool's runs of free codes, slot after slot: first code, length; 0 ends them.
    .db 0x24, 8  ; up to the colour fills: the move range's shadow tiles BG3 with 0x2C and 0x2E
    .db 0x6C, 45  ; past the battle message's first line (0x30-0x6B)
    .db 0x30, 60  ; that line: a spell list's rows take it while no battle message draws
    .db 0x33, 15  ; the windows'
    .db 0x42, 15
    .db 0x51, 15
    .db 0x00
_run_bits:
; A run's bit in panel.dirty, by run * 2.
    .db 0x01, 0x00, 0x02, 0x00, 0x04, 0x00, 0x08, 0x00, 0x10, 0x00, 0x20, 0x00
_run_bits_end:
    .assert _run_bits - _pool_runs - 1 == _run_bits_end - _run_bits, "a dirty bit for every pool run"
}
