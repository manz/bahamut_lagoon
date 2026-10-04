; Naming screen

; 8x16

; String length for chapter titles (We may use a smaller font 8x8 for example)
; let the string end with 0xff
*=0xee55b3
CHAPTER_LENGTH:
;;.EE:55B3                 CMP     #$A
    nop
    nop
    nop
;
;;.EE:55B6                 BCS     loc_EE55BB
    nop
    nop

;*=0xEE55B3c
;    cmp.w #0x0f



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
__BREAKPOINT_copy_without_shift:
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
;*=0xEE55A2
; used to decide where the next char would go 0 0x20, 0x60  [naming]
;  .EE:55A2                 LDA     word_EE548C, X
;    lda.l char_offset_table, x

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
;*=0xee5460
; .EE:5460                 LDA     word_EE548C, X [messages]
;   lda.l char_offset_table, x

*=0xEE548C
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
;    .dw 0x400
;    .dw 0x420
;    .dw 0x440

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


;.EE:54D7 build_title_screen_map:                 ; CODE XREF: sub_EED44F+10P
;.EE:54D7                                         ; sub_EED4AB+10P ...
;.EE:54D7                 PHP
;.EE:54D8                 REP     #$20 ; ' '
;.EE:54DA                 ORA     byte3_7E1860+2 ; orig=0x001862
;.EE:54DE                 STA     D, word_7E0500
;.EE:54E0                 LDA     byte3_7E1860 ; orig=0x001860
;.EE:54E4                 TAX
;.EE:54E5                 LDY     #$10
;.EE:54E8
;.EE:54E8 loc_EE54E8:                             ; CODE XREF: build_title_screen_map+1Cj
;.EE:54E8                 LDA     D, word_7E0500
;.EE:54EA                 STA     byte3_7EC400, X
;.EE:54EE                 INC     D, word_7E0500
;.EE:54F0                 INX
;.EE:54F1                 INX
;.EE:54F2                 DEY
;.EE:54F3                 BNE     loc_EE54E8
; Tries change the tilemap for chapter titles -> works but breaks the message (in sprites)
;*=0xEE54E8
;{
;loop:
;    lda.b 0x00
;    sta.l 0x7ec400, x
;    inc 0x00
;    lda.b 0x00
;    sta.l 0x7ec440, x
;    inc 0x00
;
;    inx
;    inx
;    dey
;    bne loop
;    plp
;    rtl
;}
;.EE:54F5                 LDA     byte3_7E1860 ; orig=0x001860
;.EE:54F9                 CLC
;.EE:54FA                 ADC     #$40 ; '@'
;.EE:54FD                 TAX
;.EE:54FE                 LDY     #$10
;.EE:5501
;.EE:5501 loc_EE5501:                             ; CODE XREF: build_title_screen_map+35j
;.EE:5501                 LDA     D, word_7E0500
;.EE:5503                 STA     byte3_7EC400, X
;.EE:5507                 INC     D, word_7E0500
;.EE:5509                 INX
;.EE:550A                 INX
;.EE:550B                 DEY
;.EE:550C                 BNE     loc_EE5501
;.EE:550E                 PLP
;.EE:550F                 RTL


;*=0xEE51EF
;    jsr.l display_string_reloc
;    rts


;*=0xEE5409
;    pea #0
;    jsr.l display_string.entrypoint
;    pla
;    jmp.w 0xee5484 & 0xffff
