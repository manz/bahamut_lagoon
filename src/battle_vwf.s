
; 0xFA char count
; 0x1A used to store char count
; 0x18 WRAM Pointer

battle_vwf_position=0x7EBE00

;.C0:7B1A battle_string_manip:                    ; CODE XREF: sub_C074E5+8p
;.C0:7B1A                 STZ     D, byte_7E00FA
;.C0:7B1C                 LDX     #0
;.C0:7B1F                 STX     D, word_7E001C
;.C0:7B21                 STZ     D, word_7E001E+1

*=0xC07B1A
    jsr.l battle_vwf_init
    nop

    nop
    nop

    nop
    nop

*=0xC009B7
init_battle_vwf:
    jsr.l battle_vwf_init
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

*=0xC07B25
; check if we are past the end of the window
;    .C0:7B25                 CMP     #$3D ; '='
    cmp.b #0x1e*3

;.C0:0959                 STA     D,$1B
;.C0:095B                 JSR     sub_C009B7
;.C0:095E                 LDX     #0
;.C0:0961                 STX     D,$1C
;.C0:0963                 STZ     D,$1F
*=0xC09BE1
rts
wait_for_something__long:
jsr.w 0xC006AC
rtl
