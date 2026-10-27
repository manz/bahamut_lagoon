"""
Load screen save slot header, laid out for the French labels.

The vanilla code places each piece with `lda #offset` / `jsr 0x495B` (byte offset in the slot's BG2 tilemap, two
bytes a tile), then prints it. "Chapitre" is one letter longer than "CHAPTER", and "TEMPS   :  :  " carries the
time's colons for a start one tile left of "TIME".

The chapter titles take TITLE_COLUMNS (text_buffer_vwf.s) instead of 16, so each slot's header starts three tiles
further left, in the room left of the cursor, the cursor with it. Their tiles move to BG2 tiles the load screen
neither shows nor writes (traced in kintsuki: the title screen's art, which it decompresses again on return): 0x220-
0x27B for slots 1 and 2, 0x2C0-0x2ED for slot 3. The save screen (EEF8xx) and the naming screen keep vanilla's 16
columns at 0x120-0x17F.

The release's version (build.py: BL_VERSION, "dev" by default) is an inline string of text/inline.xml drawn top right,
in the padding the first "PAS DE DONNEES" hook leaves.
"""

.import "text_buffer_vwf"

_SHIFT = 3 * 2  ; three tiles left: column 8, so a title ends on column 30
_BG2_CHARS = 0x1000  ; VRAM word of BG2 tile 0
_TITLE_TILES = 2 * TITLE_COLUMNS
_SLOT_1_TILES = 0x220
_SLOT_2_TILES = _SLOT_1_TILES + _TITLE_TILES
_SLOT_3_TILES = 0x2C0
_CURSOR_X = 0x54 - _SHIFT * 4  ; the cursor sprite's x on a slot (EED27C: x, then y, by entry)


; Slot 1 (EED44F), 2 (EED4AB) and 3 (EED507): title, "Chapitre", number and "Temps" from the slot's corner, the
; title in the wide layout from its own tiles.
.alloc at 0xEED456 {
    lda.w #0x00D6 - _SHIFT
}
.alloc at 0xEED45C {
    lda.w #_SLOT_1_TILES
    jsr.l wide_title_map
}
.alloc at 0xEED46A {
    lda.w #0x0096 - _SHIFT
}
.alloc at 0xEED482 {
    lda.w #0x015C - _SHIFT
}
.alloc at 0xEED4A0 {
    lda.w #_BG2_CHARS + _SLOT_1_TILES * 16
}
.alloc at 0xEED4B2 {
    lda.w #0x0296 - _SHIFT
}
.alloc at 0xEED4B8 {
    lda.w #_SLOT_2_TILES
    jsr.l wide_title_map
}
.alloc at 0xEED4C6 {
    lda.w #0x0256 - _SHIFT
}
.alloc at 0xEED4DE {
    lda.w #0x031C - _SHIFT
}
.alloc at 0xEED4FC {
    lda.w #_BG2_CHARS + _SLOT_2_TILES * 16
}
.alloc at 0xEED50E {
    lda.w #0x0456 - _SHIFT
}
.alloc at 0xEED514 {
    lda.w #_SLOT_3_TILES
    jsr.l wide_title_map
}
.alloc at 0xEED522 {
    lda.w #0x0416 - _SHIFT
}
.alloc at 0xEED53A {
    lda.w #0x04DC - _SHIFT
}
.alloc at 0xEED558 {
    lda.w #_BG2_CHARS + _SLOT_3_TILES * 16
}

; Chapter number, two tiles right, past "Chapitre" and a space. Each slot prints it right-aligned up to its cursor
; (EE4E4E); the header routine blanks its cells first (EE4D93), three cells from the cursor set here.
.alloc at 0xEED58A {
    lda.w #0x0012
}
.alloc at 0xEED476 {
    lda.w #0x00A6 + 4 - _SHIFT  ; slot 1
}
.alloc at 0xEED4D2 {
    lda.w #0x0266 + 4 - _SHIFT  ; slot 2
}
.alloc at 0xEED52E {
    lda.w #0x0426 + 4 - _SHIFT  ; slot 3
}

; "TEMPS": one tile left, so its colons sit between the time's digit pairs.
.alloc at 0xEED5CF {
    lda.w #0x003E
}

; An empty slot's "Aucune donnée", under the others' titles.
.alloc at 0xEED3CC {
    lda.w #0x00DA - _SHIFT
}
.alloc at 0xEED3E5 {
    lda.w #0x029A - _SHIFT
}
.alloc at 0xEED3FE {
    lda.w #0x045A - _SHIFT
}

; The cursor beside each slot.
.alloc at 0xEED280 {
    .dw _CURSOR_X
}
.alloc at 0xEED284 {
    .dw _CURSOR_X
}
.alloc at 0xEED288 {
    .dw _CURSOR_X
}
