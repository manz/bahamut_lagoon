*=0xDA3B2E
    nop
    nop
    nop

; copy__char_counter
*=0xDA3E9F
    jmp.w copy_counter

*=0xDA3CC5
    pla
    jmp.l vwf_char
return_from_vwf_char:
    rts

copy_counter:
    pha
    asl
    adc 1,s
    asl
    asl
    cmp.w 0x095F
    pla
    jmp.w 0x3EA2
