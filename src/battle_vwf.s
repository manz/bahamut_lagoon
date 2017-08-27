
battle_vwf_position=0x7EBE00

*=0xC009B7
init_battle_vwf:
    ldx.w #0x0000
    stx.w battle_vwf_position & 0xFFFF
    stx 0x18
    stz 0x1A
    rts

*=0xC009D2
    jmp.l battle_vwf_char
    return_from_battle_vwf_char:
    rts

; computes wram pointer from 0x1A (char count)
; nukes it because we use 0x18 to store just that.
*=0xC07BDE
    rts

*=0xC00961
    jsr.l battle_vwf_init

*=0xC07B46
    jmp.l battle_vwf_new_line
battle_vwf_new_line_return:
    inx
    stx 0x1c
    bra 0xC07B23
battle_vwf_window_pause:
    phx
    jsr.w 0xC09B98 & 0xFFFF
    plx
    bra battle_vwf_new_line_return
battle_secure_patch:


;.C0:0959                 STA     D,$1B
;.C0:095B                 JSR     sub_C009B7
;.C0:095E                 LDX     #0
;.C0:0961                 STX     D,$1C
;.C0:0963                 STZ     D,$1F
*=0xC09BE1
jsr.l battle_dma_transfer
rts

*=0xFEF000

;.C0:0A73
