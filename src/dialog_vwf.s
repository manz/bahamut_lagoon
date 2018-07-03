; copy__char_counter
*=0xDA3E9F
    jmp.w copy_counter
copy_counter_return:

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
    jmp.w copy_counter_return
