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

; Characters the battle message lines draw (lda #n / jsr C00959): 0x10 in vanilla, the 12px font's sixteen.
.alloc at 0xC0A69F {
    lda.b #0x20
}

.alloc at 0xC0A872 {
    lda.b #0x20
}

.alloc at 0xC0A890 {
    lda.b #0x20
}

.alloc at 0xC0B45F {
    lda.b #0x20
}

.alloc at 0xC0B4F3 {
    lda.b #0x20
}

.alloc at 0xC0B50C {
    lda.b #0x20
}

.alloc at 0xC0B612 {
    lda.b #0x20
}

.alloc at 0xC0D7AD {
    lda.b #0x20
}
