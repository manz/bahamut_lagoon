"""
Load screen save slot header, laid out for the French labels.

The vanilla code places each piece with `lda #offset` / `jsr 0x495B` (byte offset in the slot's BG2 tilemap, two
bytes a tile), then prints it. "Chapitre" is one letter longer than "CHAPTER", and "TEMPS   :  :  " carries the
time's colons for a start one tile left of "TIME".
"""


; Chapter number, two tiles right, past "Chapitre" and a space. Each slot prints it right-aligned up to its cursor
; (EE4E4E); the header routine blanks its cells first (EE4D93), three cells from the cursor set here.
.alloc at 0xEED58A {
    lda.w #0x0012
}
.alloc at 0xEED476 {
    lda.w #0x00A6 + 4  ; slot 1
}
.alloc at 0xEED4D2 {
    lda.w #0x0266 + 4  ; slot 2
}
.alloc at 0xEED52E {
    lda.w #0x0426 + 4  ; slot 3
}

; "TEMPS": one tile left, so its colons sit between the time's digit pairs.
.alloc at 0xEED5CF {
    lda.w #0x003E
}
