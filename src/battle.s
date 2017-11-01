
;.C0:E0D6                 LDA     #6
*=0xc0e0d6
    lda.b #7

; battle command pointer X / right window
; .C0:CA31                 LDA     #$A5 ; 'Ñ'
*=0xc0ca31
    lda.b #0xa5-8

; battle command pointer X / left window
; .C0:CA41                 LDA     #$15
*=0xc0ca41
    lda.b #0x15-8

; window position but not the content position
; .C0:CA3E                 LDY     #$4108
;*=0xc0ca3e
;    ldy.w #0x4108+0x02

; .C0:E0B5                 ADC     #$46 ; 'F
*=0xc0e0b5
    adc.w #0x46 - 2

; number of chars to prepare
; number of chars allowed for message
;.C0:D768                 LDA     #$10
*=0xc0d768
    lda.b #0x20 ; double it for now
;.C0:D7C5                 LDA     #$10
*=0xc0D7C5
    lda.b #0x20 ; double it for now

; number of char to draw
;.C0:D741                 LDA     #$10
*=0xc0D741
    lda.b #0x20
