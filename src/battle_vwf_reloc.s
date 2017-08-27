read_base_address=assets_vwf_bin


battle_dma_transfer:
{
    rep #0x21
    lda.l battle_vwf_position

    and #0xfff8
;    bit.w #3
;    bne even_char
;    and #0xfff0
even_char:
    sta.b 0x10
    asl
    clc
    adc.w #0xD000

    sta.w 0x4302

    lda 0x10
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
    rtl
}

battle_vwf_init:
    stx 0x1c
    stz 0x1f
    stx.w battle_vwf_position & 0xffff
    rtl

battle_vwf_new_line:
{
;    jmp.l battle_vwf_new_line_return

    rep #0x20
    lda.l battle_vwf_position
    and.w #0xfff8

    cmp.w #0x00e8 + 1
    bcs line2
    lda.w #0x0f << 4
    bra end

line2:
    cmp.w #0x00e8 * 2 + 1
    bcs line3
    lda.w #0x0f * 2 << 4
    bra end
line3:
    cmp.w #0x00e8 * 3 + 1
    bcs line4
    lda.w #0x0f * 3 << 4
    bra end

line4:
    lda.w #0x0f * 4 << 4
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
    and #0xfff8
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
    lda.l assets_vwf_bin + 16, x
;    lda.b #0x07
    plb

    rep #0x20
    and.w #0x00ff
    clc
    adc.l battle_vwf_position
    inc
    sta.l battle_vwf_position
;    and.w #0x3ff8
;    lsr
;    lsr
;    lsr


    sep #0x20
;    dec
;lada:
;    inc 0xfa
;    sta.b 0xfa
;    inc 0x1a
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
