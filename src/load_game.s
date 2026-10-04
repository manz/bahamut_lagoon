.scope load_game {
*=0xEE51EF
display_char_load_game:
{
  php
  position = 0x12
  write_base_address_low = 0x0020
  jsr.w compute_char_position

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
end:
  jsr.w add_letter_length
  plp
  rts

shift_copy:
  phx
  tax
  lda.l shift_table, x
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
   ;jsr.w make_shadow_20

    ;reloads the line data
    rep #0x20
    lda.l 0x004216
    sep #0x20
    xba

    ora.w write_base_address_low, y
    sta.w write_base_address_low, y
    ;jsr.w make_shadow_0

    inx
    iny
    iny

    pla
    dec
    bne shift_copy_loop
  }
    plx
    bra end

raw_copy:
  bra end

add_letter_length:
    lda.l read_base_address + 16, x
    rep #0x20
    and.w #0x00ff

    clc
    adc.w position
;    inc
    sta.w position

    plb
    sep #0x20

    rts

compute_char_position:
  pha
  sta.l 0x004202
  lda #17
  sta.l 0x004203
  nop
  nop
  rep #0x20
  lda.l 0x004216
  tax
  pla
  rts
}
}
;
;.EE:51EF display_char_load_game:                                               ; CODE XREF: sub_EE515C:loc_EE5172↑p
;.EE:51EF                                                                       ; .EE:55AC↓p
;.EE:51EF                 PHP                                                   ; Also used in the seller screen, and the "team menu"
;.EE:51EF                                                                       ; They already share the display_inline_string function
;.EE:51EF                                                                       ; It should belong to the same team.
;.EE:51F0                 REP     #$20 ; ' '
;.EE:51F2                 LDA     D, word_7E0512
;.EE:51F4                 AND     #1
;.EE:51F7                 BEQ     loc_EE51FB
;.EE:51F9                 BRA     loc_EE5200
;.EE:51FB ; ---------------------------------------------------------------------------
;.EE:51FB
;.EE:51FB loc_EE51FB:                                                           ; CODE XREF: display_char_load_game+8↑j
;.EE:51FB                 JSR     sub_EE5207
;.EE:51FE                 BRA     loc_EE5205
;.EE:5200 ; ---------------------------------------------------------------------------
;.EE:5200
;.EE:5200 loc_EE5200:                                                           ; CODE XREF: display_char_load_game+A↑j
;.EE:5200                 JSR     sub_EE5283
;.EE:5203                 BRA     loc_EE5205
;.EE:5205 ; ---------------------------------------------------------------------------
;.EE:5205
;.EE:5205 loc_EE5205:                                                           ; CODE XREF: display_char_load_game+F↑j
;.EE:5205                                                                       ; display_char_load_game+14↑j
;.EE:5205                 PLP
;.EE:5206                 RTS
;.EE:5206 ; End of function display_char_load_game
;.EE:5206
;.EE:5207 .A16
;.EE:5207 .I16
;.EE:5207
;.EE:5207 ; =============== S U B R O U T I N E =======================================
;.EE:5207
;.EE:5207
;.EE:5207 sub_EE5207:                                                           ; CODE XREF: display_char_load_game:loc_EE51FB↑p
;.EE:5207                 PHP
;.EE:5208                 SEP     #$20 ; ' '
;.EE:520A .A8
;.EE:520A                 LDA     #$7E ; '~'
;.EE:520C                 PHA
;.EE:520D                 PLB
;.EE:520E                 LDA     #$C
;.EE:5210                 STA     D, word_7E0500
;.EE:5212                 LDY     #0
;.EE:5215                 LDX     D, word_7E051C
;.EE:5217
;.EE:5217 loc_EE5217:                                                           ; CODE XREF: sub_EE5207+77↓j
;.EE:5217                 LDA     [D, word_7E0518], Y
;.EE:5219                 LSR
;.EE:521A                 STA     Native_mode_RESET, X
;.EE:521D                 STA     Native_mode_RESET+1, X
;.EE:5220                 INY
;.EE:5221                 LDA     [D, word_7E0518], Y
;.EE:5223                 LSR
;.EE:5224                 STA     word_7E0020, X
;.EE:5227                 STA     word_7E0020+1, X
;.EE:522A                 INY
;.EE:522B                 DEY
;.EE:522C                 DEY
;.EE:522D                 LDA     [D, word_7E0518], Y
;.EE:522F                 EOR     #$FF
;.EE:5231                 AND     Native_mode_RESET, X
;.EE:5234                 STA     Native_mode_RESET, X
;.EE:5237                 LDA     [D, word_7E0518], Y
;.EE:5239                 EOR     #$FF
;.EE:523B                 AND     Native_mode_RESET+1, X
;.EE:523E                 STA     Native_mode_RESET+1, X
;.EE:5241                 LDA     [D, word_7E0518], Y
;.EE:5243                 ORA     Native_mode_RESET, X
;.EE:5246                 STA     Native_mode_RESET, X
;.EE:5249                 INY
;.EE:524A                 LDA     [D, word_7E0518], Y
;.EE:524C                 EOR     #$FF
;.EE:524E                 AND     word_7E0020, X
;.EE:5251                 STA     word_7E0020, X
;.EE:5254                 LDA     [D, word_7E0518], Y
;.EE:5256                 EOR     #$FF
;.EE:5258                 AND     word_7E0020+1, X
;.EE:525B                 STA     word_7E0020+1, X
;.EE:525E                 LDA     [D, word_7E0518], Y
;.EE:5260                 ORA     word_7E0020, X
;.EE:5263                 STA     word_7E0020, X
;.EE:5266                 INY
;.EE:5267                 INX
;.EE:5268                 INX
;.EE:5269                 LDA     D, word_7E0500
;.EE:526B                 CMP     #5
;.EE:526D                 BNE     loc_EE527A
;.EE:526F                 REP     #$20 ; ' '
;.EE:5271 .A16
;.EE:5271                 LDA     D, word_7E051C
;.EE:5273                 CLC
;.EE:5274                 ADC     #$200
;.EE:5277                 TAX
;.EE:5278                 SEP     #$20 ; ' '
;.EE:527A .A8
;.EE:527A
;.EE:527A loc_EE527A:                                                           ; CODE XREF: sub_EE5207+66↑j
;.EE:527A                 DEC     D, word_7E0500
;.EE:527C                 BEQ     loc_EE5281
;.EE:527E                 JMP     loc_EE5217
;.EE:5281 ; ---------------------------------------------------------------------------
;.EE:5281
;.EE:5281 loc_EE5281:                                                           ; CODE XREF: sub_EE5207+75↑j
;.EE:5281                 PLP
;.EE:5282 .A16
;.EE:5282                 RTS
;.EE:5282 ; End of function sub_EE5207
;.EE:5282
;.EE:5283 .A16
;.EE:5283 .I16
;.EE:5283
;.EE:5283 ; =============== S U B R O U T I N E =======================================
;.EE:5283
;.EE:5283
;.EE:5283 sub_EE5283:                                                           ; CODE XREF: display_char_load_game:loc_EE5200↑p
;.EE:5283                 PHP
;.EE:5284                 SEP     #$20 ; ' '
;.EE:5286 .A8
;.EE:5286                 LDA     #$7E ; '~'
;.EE:5288                 PHA
;.EE:5289                 PLB
;.EE:528A                 LDA     #$C
;.EE:528C                 STA     D, word_7E0500
;.EE:528E                 LDY     #0
;.EE:5291                 LDX     D, word_7E051C
;.EE:5293
;.EE:5293 loc_EE5293:                                                           ; CODE XREF: sub_EE5283+A5↓j
;.EE:5293                 LDA     [D, word_7E0518], Y
;.EE:5295                 STA     D, word_7E0502
;.EE:5297                 STA     D, word_7E0504
;.EE:5299                 ASL     D, word_7E0504
;.EE:529B                 ASL     D, word_7E0504
;.EE:529D                 ASL     D, word_7E0504
;.EE:529F                 ASL     D, word_7E0504
;.EE:52A1                 LSR     D, word_7E0502
;.EE:52A3                 LSR     D, word_7E0502
;.EE:52A5                 LSR     D, word_7E0502
;.EE:52A7                 LSR     D, word_7E0502
;.EE:52A9                 INY
;.EE:52AA                 LDA     [D, word_7E0518], Y
;.EE:52AC                 LSR
;.EE:52AD                 LSR
;.EE:52AE                 LSR
;.EE:52AF                 LSR
;.EE:52B0                 ORA     D, word_7E0504
;.EE:52B2                 STA     D, word_7E0504
;.EE:52B4                 INY
;.EE:52B5                 LDA     D, word_7E0502
;.EE:52B7                 LSR
;.EE:52B8                 ORA     Native_mode_RESET, X
;.EE:52BB                 STA     Native_mode_RESET, X
;.EE:52BE                 LDA     D, word_7E0504
;.EE:52C0                 LSR
;.EE:52C1                 ORA     word_7E0020, X
;.EE:52C4                 STA     word_7E0020, X
;.EE:52C7                 LDA     D, word_7E0502
;.EE:52C9                 LSR
;.EE:52CA                 ORA     Native_mode_RESET+1, X
;.EE:52CD                 STA     Native_mode_RESET+1, X
;.EE:52D0                 LDA     D, word_7E0504
;.EE:52D2                 LSR
;.EE:52D3                 ORA     word_7E0020+1, X
;.EE:52D6                 STA     word_7E0020+1, X
;.EE:52D9                 LDA     D, word_7E0502
;.EE:52DB                 EOR     #$FF
;.EE:52DD                 AND     Native_mode_RESET, X
;.EE:52E0                 STA     Native_mode_RESET, X
;.EE:52E3                 LDA     D, word_7E0502
;.EE:52E5                 EOR     #$FF
;.EE:52E7                 AND     Native_mode_RESET+1, X
;.EE:52EA                 STA     Native_mode_RESET+1, X
;.EE:52ED                 LDA     D, word_7E0502
;.EE:52EF                 ORA     Native_mode_RESET, X
;.EE:52F2                 STA     Native_mode_RESET, X
;.EE:52F5                 LDA     D, word_7E0504
;.EE:52F7                 EOR     #$FF
;.EE:52F9                 AND     word_7E0020, X
;.EE:52FC                 STA     word_7E0020, X
;.EE:52FF                 LDA     D, word_7E0504
;.EE:5301                 EOR     #$FF
;.EE:5303                 AND     word_7E0020+1, X
;.EE:5306                 STA     word_7E0020+1, X
;.EE:5309                 LDA     D, word_7E0504
;.EE:530B                 ORA     word_7E0020, X
;.EE:530E                 STA     word_7E0020, X
;.EE:5311                 INX
;.EE:5312                 INX
;.EE:5313                 LDA     D, word_7E0500
;.EE:5315                 CMP     #5
;.EE:5317                 BNE     loc_EE5324
;.EE:5319                 REP     #$20 ; ' '
;.EE:531B .A16
;.EE:531B                 LDA     D, word_7E051C
;.EE:531D                 CLC
;.EE:531E                 ADC     #$200
;.EE:5321                 TAX
;.EE:5322                 SEP     #$20 ; ' '
;.EE:5324 .A8
;.EE:5324
;.EE:5324 loc_EE5324:                                                           ; CODE XREF: sub_EE5283+94↑j
;.EE:5324                 DEC     D, word_7E0500
;.EE:5326                 BEQ     loc_EE532B
;.EE:5328                 JMP     loc_EE5293
;.EE:532B ; ---------------------------------------------------------------------------
;.EE:532B
;.EE:532B loc_EE532B:                                                           ; CODE XREF: sub_EE5283+A3↑j
;.EE:532B                 PLP
;.EE:532C .A16
;.EE:532C                 RTS
