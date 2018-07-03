read_base_address=assets_vwf_bin


battle_dma_transfer:
{
    phb
    lda.b #0x00
    pha
    plb

    jsr.l wait_for_something__long ; vblank ?

    rep #0x21
    lda.l battle_vwf_position
    and #0xfff8
    asl

    sta.b 0x10
    asl
    clc
    adc.w #0xD000
    sta.w 0x4302

    lda.b 0x10
    clc
    adc.w #0x4180
    sta.w 0x2116

    sep #0x20

    lda #0x7E

    sta 0x4304
    ldx.w #0x00c0
    stx 0x4305
    lda #1
    sta 0x420b
    plb
    rtl
}

battle_vwf_init:
    pha
    phx
    php
    rep #0x20
    lda.w #0x0000
    sta.l battle_vwf_position
    tax
    stx 0x18
    stx 0x1c
    stz 0x1f

    plp
    plx
    pla
    rtl

battle_vwf_new_line:
{

    rep #0x20
    lda.l battle_vwf_position

    cmp.w #0x1e << 3
    bpl line2
    lda.w #0x1e << 3
    bra end

    line2:
    cmp.w #0x3c << 3
    bpl line3
    lda.w #0x3c << 3
    bra end

    line3:
    lda.w #0x0000
    bra change_window
    bra end

change_window:
    sta.l battle_vwf_position
    sep #0x20
    jmp.l battle_vwf_window_pause
end:
    sta.l battle_vwf_position
    sep #0x20
    jmp.l battle_vwf_new_line_return
}

battle_vwf_char:
{
    phb
    lda #0x7E
    pha
    plb

    lda 0x1e

    sta.l 0x004202
    lda #17
    sta.l 0x004203
    nop
    nop
    rep #0x20
    lda.l 0x004216
    tax

    lda.l battle_vwf_position
    pha
    and #0x3ff8
    asl
    asl
    tay
    pla
    and.w #0x0007
    sep #0x20
    bne shift_copy
    jmp.w raw_copy


shift_copy:
    phx
    tax
    lda.l shift_table, x
    plx
    sta.l 0x004202

    lda #0x10
    sta 0x08
    phx

shift_copy_loop:
    lda.l assets_vwf_bin, x
    sta.l 0x004203
    nop
    nop
    rep #0x20
    lda.l 0x004216
    sep #0x20
    sta.w 0x0020 + 0xD000, y
    xba
    ora.w 0x0000 + 0xD000, y
    sta.w 0x0000 + 0xD000, y
    inx
    iny
    iny

    dec 0x08
    bne shift_copy_loop
    plx
    jmp.w add_letter_length

raw_copy:
    lda.b #0x10
    sta 0x08
    phx
raw_copy_loop:
    lda.l assets_vwf_bin, x
    sta.w 0x0000 + 0xD000, y
    inx
    iny
    iny
    dec 0x08
    bne raw_copy_loop
    plx

add_letter_length:
    pha
    phx
    ; do the dma transfer before incrementing battle_dma_transfer
    jsr.l battle_dma_transfer
    plx
    pla
    lda.l assets_vwf_bin + 16, x
    plb

    rep #0x20
    and.w #0x00ff
    clc
    adc.l battle_vwf_position
    inc
    sta.l battle_vwf_position

    sep #0x20
    jmp.l return_from_battle_vwf_char

shift_table:
    .db 0
    .db 0x80
    .db 0x40
    .db 0x20
    .db 0x10
    .db 0x08
    .db 0x04
    .db 0x02
end_of_code:
}
