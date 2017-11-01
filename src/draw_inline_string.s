
; move this function inside the shift-jis lookup table might break a thing or two
*=0xEE4AE8
draw_inline_string_patched:
{
inline_string_bank_reloc=0xfd

    php
    rep #0x20
    pha
    phx
    phy
    phb
; get the pointer from A and store it in Y
; (inline_string_bank_reloc << 16) + Y
    phk
    plb

    lda 0x09, s
    pha
    dec
    tay
    pla
    inc
    inc
    sta 0x09, s ; sets the return address past the pointer where a bra waits for us.

    ; read pointer from stack return address
    lda.w 0x0002, y
    tax

; get the destination pointer
    lda.l 0x001860
;    dec
;    dec
    tay
    sep #0x20

    lda.b #0x7e
    pha
    plb
    rep #0x20

_loop:
    lda.l inline_string_bank_reloc << 16, x
    and.w #0x00ff
    cmp.w #0x00ff
    beq _end

    ora.l 0x001862
    sta.w 0xc400, y

    lda.w #0x0000
    sta.w 0xc3c0, y

    iny
    iny
    inx

    bra _loop
_end:
    sep #0x20
    tya
    sta.l 0x001860
    lda.b #1
    sta.l 0x00185A
    rep #0x20
    plb
    ply
    plx
    pla
    plp
    rts
}

;.EE:4A1E draw_inline_string:                     ; CODE XREF: .EE:6F6Cp
;.EE:4A1E                                         ; .EE:loc_EE6FABp ...
;.EE:4A1E                 PHP
;.EE:4A1F                 REP     #$20 ; ' '
;.EE:4A21                 PHA
;.EE:4A22                 PHX
;.EE:4A23                 PHY
;.EE:4A24                 PHB
;.EE:4A25                 SEP     #$20 ; ' '
;.EE:4A27 .A8
;.EE:4A27                 PHK
;.EE:4A28                 PLB
;.EE:4A29 ; ds=EE000 B=EE
;.EE:4A29                 REP     #$20 ; ' '
;.EE:4A2B .A16
;.EE:4A2B                 LDA     S, 9            ; reads jsr return address from the stack
;.EE:4A2D                 DEC
;.EE:4A2E                 TAY
;.EE:4A2F                 LDA     byte3_7E1860 ; orig=0x001860
;.EE:4A33                 DEC
;.EE:4A34                 DEC
;.EE:4A35                 TAX
;.EE:4A36
;.EE:4A36 loc_EE4A36:                             ; CODE XREF: draw_inline_string+53j
;.EE:4A36                                         ; draw_inline_string+64j ...
;.EE:4A36                 INX
;.EE:4A37                 INX
;.EE:4A38                 INY
;.EE:4A39                 INY
;.EE:4A3A                 LDA     word_EE0000, Y
;.EE:4A3D                 AND     #$FF
;.EE:4A40                 CMP     #$FF
;.EE:4A43                 BEQ     loc_EE4AAA
;.EE:4A45                 LDA     word_EE0000, Y
;.EE:4A48                 CMP     #$4081          ; space
;.EE:4A4B                 BEQ     loc_EE4A9D
;.EE:4A4D                 JSR     inline_string_lookup_char
;.EE:4A50                 CMP     #$33 ; '3'
;.EE:4A53                 BCS     loc_EE4A73
;.EE:4A55                 CMP     #$29 ; ')'
;.EE:4A58                 BCS     loc_EE4A84
;.EE:4A5A                 CLC
;.EE:4A5B                 ADC     #$33 ; '3'
;.EE:4A5E                 ORA     byte3_7E1860+2 ; orig=0x001862
;.EE:4A62                 STA     byte3_7EC400, X
;.EE:4A66                 LDA     #$31 ; '1'
;.EE:4A69                 ORA     byte3_7E1860+2 ; orig=0x001862
;.EE:4A6D                 STA     word_7EC3C0, X
;.EE:4A71                 BRA     loc_EE4A36
;.EE:4A73 ; ---------------------------------------------------------------------------
;.EE:4A73
;.EE:4A73 loc_EE4A73:                             ; CODE XREF: draw_inline_string+35j
;.EE:4A73                 ORA     byte3_7E1860+2 ; orig=0x001862
;.EE:4A77                 STA     byte3_7EC400, X
;.EE:4A7B                 LDA     #0
;.EE:4A7E                 STA     word_7EC3C0, X
;.EE:4A82                 BRA     loc_EE4A36
;.EE:4A84 ; ---------------------------------------------------------------------------
;.EE:4A84
;.EE:4A84 loc_EE4A84:                             ; CODE XREF: draw_inline_string+3Aj
;.EE:4A84                 CLC
;.EE:4A85                 ADC     #$29 ; ')'
;.EE:4A88                 ORA     byte3_7E1860+2 ; orig=0x001862
;.EE:4A8C                 STA     byte3_7EC400, X
;.EE:4A90                 LDA     #$32 ; '2'
;.EE:4A93                 ORA     byte3_7E1860+2 ; orig=0x001862
;.EE:4A97                 STA     word_7EC3C0, X
;.EE:4A9B                 BRA     loc_EE4A36
;.EE:4A9D ; ---------------------------------------------------------------------------
;.EE:4A9D
;.EE:4A9D loc_EE4A9D:                             ; CODE XREF: draw_inline_string+2Dj
;.EE:4A9D                 LDA     #0
;.EE:4AA0                 STA     byte3_7EC400, X
;.EE:4AA4                 STA     word_7EC3C0, X
;.EE:4AA8                 BRA     loc_EE4A36
;.EE:4AAA ; ---------------------------------------------------------------------------
;.EE:4AAA
;.EE:4AAA loc_EE4AAA:                             ; CODE XREF: draw_inline_string+25j
;.EE:4AAA                 TXA
;.EE:4AAB                 STA     byte3_7E1860 ; orig=0x001860
;.EE:4AAF                 LDA     #1
;.EE:4AB2                 STA     byte3_7E185A ; orig=0x00185A
;.EE:4AB6                 REP     #$20 ; ' '
;.EE:4AB8                 TYA
;.EE:4AB9                 INC
;.EE:4ABA                 STA     S, 9
;.EE:4ABC                 PLB
;.EE:4ABD ; ds=0 B=0
;.EE:4ABD
;.EE:4ABD loc_EE4ABD:                             ; CODE XREF: sub_EEFF89+AP
;.EE:4ABD                 PLY
;.EE:4ABE                 PLX
;.EE:4ABF                 PLA
;.EE:4AC0                 PLP
;.EE:4AC1                 RTS
;.EE:4AC1 ; End of function draw_inline_string
