"""Battle message layout: room for the French messages' characters."""

; Characters a message prepares (C0D768, C0D7C5) and draws (C0D741): 0x10 in vanilla.
.alloc at 0xC0D768 {
    lda.b #0x20
}

.alloc at 0xC0D7C5 {
    lda.b #0x20
}

.alloc at 0xC0D741 {
    lda.b #0x20
}
