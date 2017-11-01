; Naming screen

; 8x16

; nukes the odd/even char for japanese chars 12px.
*=0xee51F4
;.EE:51F4                 AND     #1
    nop
    nop
    nop

;.EE:51F7                 BEQ     loc_EE51FB
    nop
    nop

; replaces the copy_without shift
*=0xee5283
    php
    sep #0x20
    lda #0x7e
    pha
    plb
    lda #8
    sta 0x00
    ldy.w #0
    ldx 0x1c
{
loop:
    lda [0x18], y
    sta.w 0x0000, x

    iny
    inx
    inx

    dec 0x00
    bne loop
}
{
    lda #8
    sta 0x00
    ldx 0x1c
loop:
    lda [0x18], y
    sta.w 0x0200, x
    iny
    inx
    inx

    dec 0x00
    bne loop
}
    plp
    rts

; Used to compute the char address in font [naming]
*=0xEE558A
    lda.w #17 ; char height

; FIXME: Remove when char_offset_table is patched in place
*=0xEE55A2
; used to decide where the next char would go 0 0x20, 0x60  [naming]
;  .EE:55A2                 LDA     word_EE548C, X
    lda.l char_offset_table, x

; change character pixel width for cursor position computation in naming screen.
*=0xeedbf5
;.EE:DBF5                 LDA     #0xC
    lda #0x0008


; save screen
; need to shift
;.EE:5448                 LDA     #0x18 [messages]
*=0xee5448
    lda.w #17

; FIXME: Remove when char_offset_table is patched in place
*=0xee5460
; .EE:5460                 LDA     word_EE548C, X [messages]
   lda.l char_offset_table, x

*=0xEE548C
; may be patched at it's original position.
char_offset_table:
    .dw 0
    .dw 0x20
    .dw 0x20 * 2
    .dw 0x20 * 3
    .dw 0x20 * 4
    .dw 0x20 * 5
    .dw 0x20 * 6
    .dw 0x20 * 7
    .dw 0x20 * 8
    .dw 0x20 * 9
    .dw 0x20 * 10
    .dw 0x20 * 11
    .dw 0x20 * 12
    .dw 0x20 * 13
    .dw 0x20 * 14
    .dw 0x20 * 15
    .dw 0x20 * 16
    .dw 0x20 * 17
    .dw 0x20 * 18

;.EE:548C word_EE548C:    .WORD 0                 ; DATA XREF: .EE:5460r
;.EE:548E                 .WORD 0x20
;.EE:5490                 .WORD 0x60
;.EE:5492                 .WORD 0x80
;.EE:5494                 .WORD 0xC0
;.EE:5496                 .WORD 0xE0
;.EE:5498                 .WORD 0x120
;.EE:549A                 .WORD 0x140
;.EE:549C                 .WORD 0x180
;.EE:549E                 .WORD 0x1A0
;.EE:54A0                 .WORD 0x400
;.EE:54A2                 .WORD 0x420
;.EE:54A4                 .WORD 0x460
;.EE:54A6                 .WORD 0x480
;.EE:54A8                 .WORD 0x4C0
;.EE:54AA                 .WORD 0x4E0
;.EE:54AC                 .WORD 0x520
;.EE:54AE                 .WORD 0x540
;.EE:54B0                 .WORD 0x580
;.EE:54B2                 .WORD 0x5A0
