"""Load game screen variable-width font routines, relocated to bank ED."""

.include "src/ed_reloc.i"
.include "src/wram.i"

.import "vwf_font"


.reserve load_game_vwf_position 2 at 0x7E051C in wram  ; save slot name pixel position

.alloc load_game_reloc in ed_reloc {
    .scope load_game {
    """Save slot names drawn with the variable-width font."""
    vwf_return = 0xee5484
vwf_entry_point:
    ldy.b 0x0512
    lda.w #0x0000
    sta.w load_game_vwf_position
loop:
    lda [0x14], y
    and.w #0x00ff
    cmp.w #0x00ff
    beq exit
;; compute char pointer
    sep.b #0x20
    sta.l 0x004202
    lda #17
    sta.l 0x004203
    nop
    nop

    rep #0x20
    lda.l 0x004216
    tax

    phy

    lda.w load_game_vwf_position

    pha
    and #0xfff8
    asl
    asl
    tay
    pla
    and.w #7
    beq raw_copy
    jmp.w shift_copy

copy_return:
    ply
    iny
; bra raw_copy
    bra loop
exit:
    jmp.l vwf_return

raw_copy:
    lda.w #0x08
    phx
raw_copy_loop:
    pha
    lda.l assets_vwf_bin, x
    sta 0x7800, y
    sta 0x7801, y
    lda.l assets_vwf_bin + 8, x
    sta.w 0x7800 + 0x20, y
    sta.w 0x7801 + 0x20, y
    inx
    iny
    iny
    pla
    dec
    bne raw_copy_loop
    plx
    jsr.w add_letter_length
    bra copy_return

shift_copy:
    phx

    tax
    sep #0x20

    lda.l shift_table, x
    plx
    sta.l 0x004202

    lda.b #0x10
    phx
shift_copy_loop:
    pha
    lda.l assets_vwf_bin, x
    sta.l 0x004203
    nop
    nop

    rep #0x20
    lda.l 0x004216
    sep #0x20

    ora.w 0x7800 + 0x20, y
    sta.w 0x7800 + 0x20, y
    sta.w 0x7800 + 0x20 + 1, y

    rep #0x20
    lda.l 0x004216
    sep #0x20
    xba

    ora 0x7800, y
    sta 0x7800, y
    sta.w 0x7800 + 1, y

    inx
    iny
    iny
    pla
    dec
    bne shift_copy_loop
    plx
    rep #0x20
    jsr.w add_letter_length

    bra copy_return

add_letter_length:
    lda.l assets_vwf_bin + 16, x
; lda.w #0x0008
    and.w #0x00ff

    sec
    adc.w load_game_vwf_position
    sta.w load_game_vwf_position
    _bp_position_update:  ; breakpoint anchor
    rts

shift_table:
    .db 0x00  ; for debug purposes
    .db 0x80
    .db 0x40
    .db 0x20
    .db 0x10
    .db 0x08
    .db 0x04
    .db 0x02
    }
}
