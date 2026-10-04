;.EE:545C                 LDA     D, word_7E0512
;.EE:545E                 ASL
;.EE:545F                 TAX
;.EE:5460                 LDA     word_EE548C, X
;.EE:5464                 CLC
;.EE:5465                 ADC     #$7800

;*=0xee545c
;lda.w #0x7800
;nop
;nop
;nop
;nop
;nop
;nop
;nop
;nop
;nop
;nop

*=0xEE5409
    jmp.l load_game.vwf_entry_point

;*=0xEE554B
;  ldy.w

;.EE:554B loc_EE554B:                                                           ; CODE XREF: .EE:552E↑j
;.EE:554B                                                                       ; .EE:553F↑j
;.EE:554B                                                                       ; .EE:5586↓j
;.EE:554B                                                                       ; .EE:55B8↓j
;.EE:554B                 LDY     D, word_7E0512
;.EE:554D                 LDA     [D, word_7E0514], Y
;.EE:554F                 AND     #$FF
;.EE:5552                 CMP     #$F0
;.EE:5555                 BCC     loc_EE5588
;.EE:5557                 CMP     #$FF
;.EE:555A                 BNE     loc_EE555F
;.EE:555C

;.EE:555C loc_EE555C:
;.EE:555C                 JMP     loc_EE55BB
;.EE:555F ; ---------------------------------------------------------------------------
;.EE:555F
;.EE:555F loc_EE555F:                                                           ; CODE XREF: .EE:555A↑j
;.EE:555F                 LDX     #0
;.EE:5562                 CMP     #$F0
;.EE:5565                 BEQ     loc_EE5582
;.EE:5567                 LDX     #$1800
;.EE:556A                 CMP     #$F1
;.EE:556D                 BEQ     loc_EE5582
;.EE:556F                 LDX     #$3000
;.EE:5572                 CMP     #$F2
;.EE:5575                 BEQ     loc_EE5582
;.EE:5577                 LDX     #$4800
;.EE:557A                 CMP     #$F3
;.EE:557D                 BEQ     loc_EE5582
;.EE:557F                 LDX     #0
;.EE:5582
;.EE:5582 loc_EE5582:                                                           ; CODE XREF: .EE:5565↑j
;.EE:5582                                                                       ; .EE:556D↑j
;.EE:5582                                                                       ; .EE:5575↑j
;.EE:5582                                                                       ; .EE:557D↑j
;.EE:5582                 STX     D, word_7E051E
;.EE:5584                 INC     D, word_7E0514
;.EE:5586                 BRA     loc_EE554B
;.EE:5588 ; ---------------------------------------------------------------------------
;.EE:5588
;.EE:5588 loc_EE5588:                                                           ; CODE XREF: .EE:5555↑j
;.EE:5588                 STA     D, word_7E0500                                ; save current char
;.EE:558A                 LDA     #$18
;.EE:558D                 JSR     multiply_8_16
;.EE:5590                 CLC
;.EE:5591                 ADC     D, word_7E051E
;.EE:5593                 CLC
;.EE:5594                 ADC     #0
;.EE:5597                 STA     D, word_7E0518
;.EE:5599                 LDA     #$ED
;.EE:559C

;.EE:559C loc_EE559C:
;.EE:559C                 STA     D, word_7E051A
;.EE:559E                 LDA     D, word_7E0512
;.EE:55A0                 ASL
;.EE:55A1                 TAX
;.EE:55A2                 LDA     word_EE548C, X
;.EE:55A6                 CLC
;.EE:55A7                 ADC     #$7800
;.EE:55AA                 STA     D, word_7E051C
;.EE:55AC                 JSR     display_char_load_game
;.EE:55AF                 INC     D, word_7E0512
;.EE:55B1                 LDA     D, word_7E0512
;.EE:55B3                 CMP     #$A
;.EE:55B6

;.EE:55B6 loc_EE55B6:
;.EE:55B6                 BCS     loc_EE55BB
;.EE:55B8                 JMP     loc_EE554B
;.EE:55BB ; ---------------------------------------------------------------------------
;.EE:55BB
;.EE:55BB loc_EE55BB:                                                           ; CODE XREF: .EE:loc_EE555C↑j
;.EE:55BB                                                                       ; .EE:loc_EE55B6↑j
;.EE:55BB                 LDA     D, word_7E051C                                ; manipulates 0x7e051c value in A register but does not care for the result?
;.EE:55BD                 SEC
;.EE:55BE                 SBC     #$7800
;.EE:55C1                 LSR
;.EE:55C2                 CLC
;.EE:55C3                 LDA     D, unk_7E0532+2
;.EE:55C5                 STA     D, word_7E0500
;.EE:55C7                 LDA     word_7E19FF+1 ; orig=0x001A00
;.EE:55CB                 TAX
;.EE:55CC                 LDA     #$8000
;.EE:55CF                 STA     word_7E0006, X ; orig=0x0006
;.EE:55D3                 LDA     D, word_7E0500
;.EE:55D5                 STA     word_7E0002+1, X ; orig=0x0003
;.EE:55D9                 LDA     #$200
;.EE:55DC                 STA     word_7E0004+1, X ; orig=0x0005
;.EE:55E0                 LDA     #$7E ; '~'
;.EE:55E3                 XBA
;.EE:55E4                 STA     Native_mode_RESET+1, X ; orig=0x0001
;.EE:55E8                 LDA     #$7800
;.EE:55EB                 STA     Native_mode_RESET, X ; orig=0x0000
;.EE:55EF                 TXA
;.EE:55F0                 CLC
;.EE:55F1                 ADC     #8
;.EE:55F4                 TAX
;.EE:55F5                 LDA     #$8000
;.EE:55F8                 STA     word_7E0006, X ; orig=0x0006
;.EE:55FC                 LDA     D, word_7E0500
;.EE:55FE                 CLC
;.EE:55FF                 ADC     #$100
;.EE:5602                 STA     word_7E0002+1, X ; orig=0x0003
;.EE:5606                 LDA     #$200
;.EE:5609                 STA     word_7E0004+1, X ; orig=0x0005
;.EE:560D                 LDA     #$7E ; '~'
;.EE:5610                 XBA
;.EE:5611                 STA     Native_mode_RESET+1, X ; orig=0x0001
;.EE:5615                 LDA     #$7800
;.EE:5618                 CLC
;.EE:5619                 ADC     #$200
;.EE:561C                 STA     Native_mode_RESET, X ; orig=0x0000
;.EE:5620                 TXA
;.EE:5621                 CLC
;.EE:5622                 ADC     #8
;.EE:5625                 STA     word_7E19FF+1 ; orig=0x001A00
;.EE:5629                 JSL     sub_EE440B
