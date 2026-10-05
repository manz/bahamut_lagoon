"""Dialog variable-width font: hooks into the dialog room text renderer."""

.extern vwf_char
.extern dialog_vwf_position

; copy__char_counter

.alloc at 0xDA3E9F {
    jmp.w copy_counter

copy_counter_return:
}
.alloc at 0xDA3CC5 {
    pla
    jmp.l vwf_char

return_from_vwf_char:
    rts

copy_counter:
    pha
    asl
    adc 1, s
    asl
    asl
    cmp.w dialog_vwf_position
    pla
    jmp.w copy_counter_return
}
