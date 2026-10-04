.EE:538C item_descriptions_copy_char:
.EE:538C                 SEP     #$20 ; ' '
.EE:538E .A8
.EE:538E                 LDA     #$7E ; '~'
.EE:5390                 PHA
.EE:5391                 PLB
.EE:5392                 REP     #$20 ; ' '
.EE:5394 .A16
.EE:5394                 LDA     #$FFFF
.EE:5397                 LDX     #$41E0
.EE:539A                 LDY     #$20 ; ' '
.EE:539D                 JSL     sub_EE3DD0 ; memset ? memset(0x7E41E0, 0xffff, 0x20)


.EE:53A1                 LDA     #0
.EE:53A4                 STA     word_7E41E6
.EE:53A8                 LDA     #1
.EE:53AB                 STA     byte3_7E182E ; orig=0x00182E
.EE:53AF                 JSL     sub_EE510A
.EE:53B3                 LDA     D, byte3_7E0532
.EE:53B5                 CMP     #$275
.EE:53B8                 BEQ     loc_EE53BE
.EE:53BA                 JSL     sub_EE440B
.EE:53BE
.EE:53BE loc_EE53BE:                             ; CODE XREF: .EE:53B8j
.EE:53BE                 LDA     #8
.EE:53C1                 STA     D, word_7E0512
.EE:53C3                 LDX     #0
.EE:53C6
.EE:53C6 loc_EE53C6:                             ; CODE XREF: .EE:53E5j
.EE:53C6                 LDA     #$80 ; 'Ç'
.EE:53C9                 STA     D, word_7E0514
.EE:53CB                 LDA     #0
.EE:53CE
.EE:53CE loc_EE53CE:                             ; CODE XREF: .EE:53D6j
.EE:53CE                 STA     word_7E7800, X
.EE:53D2                 INX
.EE:53D3                 INX
.EE:53D4                 DEC     D, word_7E0514
.EE:53D6                 BNE     loc_EE53CE
.EE:53D8                 LDA     D, byte3_7E0532
.EE:53DA                 CMP     #$275
.EE:53DD                 BEQ     loc_EE53E3
.EE:53DF                 JSL     sub_EE440B
.EE:53E3
.EE:53E3 loc_EE53E3:                             ; CODE XREF: .EE:53DDj
.EE:53E3                 DEC     D, word_7E0512
.EE:53E5                 BNE     loc_EE53C6
.EE:53E7                 STZ     D, word_7E0512
.EE:53E9                 STZ     D, word_7E051E
.EE:53EB                 LDA     #$9E00
.EE:53EE                 STA     D, word_7E0514
.EE:53F0                 LDA     #$7E ; '~'
.EE:53F3                 STA     D, word_7E0516
.EE:53F5                 LDA     D, byte3_7E0532
.EE:53F7                 CMP     #$FFFF
.EE:53FA                 BEQ     loc_EE5409
.EE:53FC                 ASL
.EE:53FD                 TAX
.EE:53FE                 LDA     item_descriptions_ptrs, X
.EE:5402                 STA     D, word_7E0514
.EE:5404                 LDA     #$EE ; '¯'
.EE:5407                 STA     D, word_7E0516
.EE:5409
.EE:5409 loc_EE5409:                             ; CODE XREF: .EE:53FAj
.EE:5409                                         ; .EE:5444j ...
.EE:5409                 LDY     D, word_7E0512
.EE:540B                 LDA     [D, word_7E0514], Y
.EE:540D                 AND     #$FF
.EE:5410                 CMP     #$F0 ; '­'
.EE:5413                 BCC     loc_EE5446
.EE:5415                 CMP     #$FF
.EE:5418                 BNE     loc_EE541D
.EE:541A                 JMP     loc_EE5484
.EE:541D ; ---------------------------------------------------------------------------
.EE:541D
.EE:541D loc_EE541D:                             ; CODE XREF: .EE:5418j
.EE:541D                 LDX     #0
.EE:5420                 CMP     #$F0 ; '­'
.EE:5423                 BEQ     loc_EE5440
.EE:5425                 LDX     #$1800
.EE:5428                 CMP     #$F1 ; '±'
.EE:542B                 BEQ     loc_EE5440
.EE:542D                 LDX     #$3000
.EE:5430                 CMP     #$F2 ; '='
.EE:5433                 BEQ     loc_EE5440
.EE:5435                 LDX     #$4800
.EE:5438                 CMP     #$F3 ; '¾'
.EE:543B                 BEQ     loc_EE5440
.EE:543D                 LDX     #0
.EE:5440
.EE:5440 loc_EE5440:                             ; CODE XREF: .EE:5423j
.EE:5440                                         ; .EE:542Bj ...
.EE:5440                 STX     D, word_7E051E
.EE:5442                 INC     D, word_7E0514
.EE:5444                 BRA     loc_EE5409
.EE:5446 ; ---------------------------------------------------------------------------
.EE:5446
.EE:5446 loc_EE5446:                             ; CODE XREF: .EE:5413j
.EE:5446                 STA     D, word_7E0500
.EE:5448                 LDA     #$18
.EE:544B                 JSR     multiply_8_16
.EE:544E                 CLC
.EE:544F                 ADC     D, word_7E051E
.EE:5451                 CLC
.EE:5452                 ADC     #0
.EE:5455                 STA     D, word_7E0518 ; font pointer
.EE:5457                 LDA     #$ED ; 'Ý'

.EE:545A                 STA     D, word_7E051A

.EE:545C                 LDA     D, word_7E0512
.EE:545E                 ASL
.EE:545F                 TAX
.EE:5460                 LDA     word_EE548C, X
.EE:5464                 CLC
.EE:5465                 ADC     #$7800
.EE:5468                 STA     D, word_7E051C
.EE:546A                 JSR     sub_EE515C
.EE:546D                 LDA     D, byte3_7E0532
.EE:546F                 CMP     #$275
.EE:5472                 BEQ     loc_EE5478
.EE:5474                 JSL     sub_EE440B
.EE:5478
.EE:5478 loc_EE5478:                             ; CODE XREF: .EE:5472j
.EE:5478                 INC     D, word_7E0512
.EE:547A                 LDA     D, word_7E0512
.EE:547C                 CMP     #$14
.EE:547F                 BCS     loc_EE5484
.EE:5481                 JMP     loc_EE5409
.EE:5484 ; ---------------------------------------------------------------------------
.EE:5484
.EE:5484 loc_EE5484:                             ; CODE XREF: .EE:541Aj
.EE:5484                                         ; .EE:547Fj
.EE:5484                 JSL     sub_EE440B
.EE:5488                 JSL     sub_EE4501
