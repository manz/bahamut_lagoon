char_count = 0xFA
text_pos = 0x1C
sub_C07B93 = 0xC07B93

battle_string_manip:                    ; CODE XREF: sub_C074E5+8p
                STZ     char_count
                LDX     #0
                STX     text_pos
                STZ     0x1F

loc_C07B23:                             ; CODE XREF: battle_string_manip+4Aj
                                        ; battle_string_manip+51j ...
                LDA     char_count
                CMP     #0x3D ; '='
                BNE     loc_C07B29

loc_C07B29:                             ; CODE XREF: battle_string_manip+Dj
                                        ; battle_string_manip+28j
                LDX     text_pos
                LDA     0x720,X
                CMP     #0xF9 ; '¨'
                BCC     loc_C07B81
                BEQ     loc_C07B66
                CMP     #0xFA ; '·'
                BEQ     loc_C07B67
                CMP     #0xFC ; '³'
                BEQ     loc_C07B75
                CMP     #0xFD ; '²'
                BEQ     loc_C07B6D
                CMP     #0xFE ; '¦'
                BCC     loc_C07B29
                BNE     locret_C07B92
                LDA     char_count
                CMP     #0x28 ; '('
                BEQ     loc_C07B61
                BCS     loc_C07B58
                CMP     #0x14
                BEQ     loc_C07B61
                BCS     loc_C07B5D
                LDA     #0x14
                BRA     loc_C07B5F
; ---------------------------------------------------------------------------

loc_C07B58:                             ; CODE XREF: battle_string_manip+32j
                PHX
                JSR     sub_C09B98
                PLX

loc_C07B5D:                             ; CODE XREF: battle_string_manip+38j
                LDA     #0x28 ; '('

loc_C07B5F:                             ; CODE XREF: battle_string_manip+3Cj
                STA     char_count

loc_C07B61:                             ; CODE XREF: battle_string_manip+30j
                                        ; battle_string_manip+36j
                INX
                STX     text_pos
                BRA     loc_C07B23
; ---------------------------------------------------------------------------

loc_C07B66:                             ; CODE XREF: battle_string_manip+18j
                INX

loc_C07B67:                             ; CODE XREF: battle_string_manip+1Cj
                INX
                INX
                STX     text_pos
                BRA     loc_C07B23
; ---------------------------------------------------------------------------

loc_C07B6D:                             ; CODE XREF: battle_string_manip+24j
                INX
                STX     text_pos
                JSR     sub_C07B93
                BRA     loc_C07B23
; ---------------------------------------------------------------------------

loc_C07B75:                             ; CODE XREF: battle_string_manip+20j
                INX
                LDA     0x720,X
                INX
                STX     text_pos
                JSR     sub_C07BD2
                BRA     loc_C07B23
; ---------------------------------------------------------------------------

loc_C07B81:                             ; CODE XREF: battle_string_manip+16j
;                LDA     char_count
;                STA     0x1A
;                JSR     compute_battle_char_wram_pos
                JSR     build_char_data_wram
                JSR     transfer_battle_char_vram
;                INC     char_count
                BRA     loc_C07B23
; ---------------------------------------------------------------------------

locret_C07B92:                          ; CODE XREF: battle_string_manip+2Aj
                RTS
