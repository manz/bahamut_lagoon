; Implements nop opcode in dialog room interpreter.
*=0xDA7816
opcode_9E:
  sep #0x20
  lda.b #0x01
  rts

*=0xDA405C
  .dw opcode_9E
  .dw opcode_9E ; overwrites 9F trap opcode
