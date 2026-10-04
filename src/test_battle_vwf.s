*=0xC009EC
    jmp 0x09F5

*=0xC00A00
    LDA.L 0xED0000,X
    STA.W 0x0004,Y
    JMP.W 0x0A0E

*=0xC09BEB
kabinet:
nop
nop

; multiply char count by 0x20 to have the wram pointer
; increment 0xFA should be conditional ?
; or encode bitsleft in 0xFA
*=0xC07BDE
   ; and #0b11111000
    sta 0x4202
    lda.b #0x20
    sta 0x4203
    nop
    nop
;.A16
    rep #0x21 ; '!'
    lda 0x4216
    adc #0xD000
    sta 0x18
;.A8
    sep #0x20 ; ' '
    rts


