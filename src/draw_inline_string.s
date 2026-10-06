"""
Inline menu strings: each vanilla call site (build/gen/inline_string_hooks.s) calls here with the relocated record's
pointer after the call; menu_vwf draws the record.
"""

.extern menu_draw_inline_string

; move this function inside the shift-jis lookup table might break a thing or two

.alloc at 0xEE4AE8 {
draw_inline_string_patched:
    php
    rep #0x30
    pha
    phx
    phy
    phb
    phk
    plb
    lda 0x09, s  ; the return address: the pointer follows it
    tay
    inc
    inc
    sta 0x09, s  ; return past the pointer, where a bra waits for us
    lda.w 0x0001, y
    tax
    jsl.l menu_draw_inline_string
    plb
    ply
    plx
    pla
    plp
    rts
}
