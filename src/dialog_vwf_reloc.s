write_base_address_low=0xE280 + 0x20
position=0x095f

.macro do_shadow(delta) {
    ; input: A, trashes: A
    pha
    rep #0x20
    and.w #0x00ff
    ror
    sep #0x20
    ora.w write_base_address_low + 3 + delta, y
    sta.w write_base_address_low + 3 + delta, y

    xba
    rep #0x20
    and.w #0x0080
    sep #0x20

    ora.w write_base_address_low + 1 + delta, y
    sta.w write_base_address_low + 1 + delta, y
    pla
}


vwf_char:
{
    phb
    pha
    lda #0x7e
    pha
    plb
    pla
    sta.l 0x004202
    lda #17
    sta.l 0x004203
    nop
    nop

    rep #0x20
    lda.l 0x004216
    tax

    lda.w position
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

    phx
    lda #0x10
    {
shift_copy_loop:
        pha
        lda.l read_base_address, x
        sta.l 0x004203
        nop
        nop
        rep #0x20
        lda.l 0x004216
        sep #0x20

        ora.w write_base_address_low + 0x20, y
        sta.w write_base_address_low + 0x20, y
        do_shadow(0x20)

        ;reloads the line data
        rep #0x20
        lda.l 0x004216
        sep #0x20
        xba

        ora.w write_base_address_low, y
        sta.w write_base_address_low, y
        do_shadow(0)

        inx
        iny
        iny

        pla
        dec
        bne shift_copy_loop
    }
    plx
    jmp.w add_letter_length

raw_copy:
    phx
    lda #0x10
    {
raw_copy_loop:
        pha
        lda.l read_base_address, x

        ora.w write_base_address_low, y
        sta.w write_base_address_low, y

        do_shadow(0)

        inx
        iny
        iny

        pla
        dec
        bne raw_copy_loop
    }
    plx

add_letter_length:
    lda.l read_base_address + 16, x
    rep #0x20
    and.w #0x00ff

    clc
    adc.w position
    inc
    sta.w position

    plb
    sep #0x20

    jmp.l return_from_vwf_char

shift_table:
    .db 0x00 ; for debug purposes
    .db 0x80
    .db 0x40
    .db 0x20
    .db 0x10
    .db 0x08
    .db 0x04
    .db 0x02
}

