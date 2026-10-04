; Implements nop opcode in dialog room interpreter.

.alloc at 0xDA7816 {
opcode_9E:
    sep #0x20
    lda.b #0x01
    rts
}
.alloc at 0xDA405C {
    .dw opcode_9E
    .dw opcode_9E  ; overwrites 9F trap opcode
}
