"""Battle message variable-width font routines, relocated to bank ED."""

.include "src/ed_reloc.i"
.include "src/wram.i"
.include "src/expansion.i"

.import "vwf_font"
.extern wait_for_something__long
.extern battle_vwf_window_pause
.extern battle_vwf_new_line_return
.extern return_from_battle_vwf_char
.extern panel_slots_overwritten


.reserve battle_vwf_position 2 at 0x7EBE00 in wram  ; battle text pixel position

_BUFFER = 0x7ED000  ; the engine's 2bpp text buffer, three lines of 0x1E 8x16 columns
_VRAM = 0x4180  ; word address of the buffer's first column
_LINE_BYTES = 0x1E * 0x20
_LINES = 3

.alloc battle_vwf_reloc in ed_reloc {
battle_dma_transfer:
"""Wait for vblank, then DMA the battle text buffer ($7E:D000) to VRAM at the current line."""
    {
        phb
        lda.b #0x00
        pha
        plb

        jsr.l wait_for_something__long  ; vblank ?

        rep #0x21
        lda.l battle_vwf_position
        and #0xfff8
        asl

        sta.b 0x10
        asl
        clc
        adc #0xD000
        sta 0x4302

        lda.b 0x10
        clc
        adc #0x4180
        sta 0x2116

        sep #0x20

        lda #0x7E

        sta 0x4304
        ldx.w #0x00c0
        stx 0x4305
        lda #1
        sta 0x420b
        plb
        rtl
    }

battle_vwf_init:
"""Reset the battle text position and the engine's char counters."""
    pha
    phx
    php
    rep #0x20
    lda.w #0x0000
    sta.l battle_vwf_position
    tax
    stx 0x18
    stx 0x1c
    stz 0x1f

    plp
    plx
    pla
    rtl

battle_vwf_new_line:
"""
Move to the next of the three battle text lines; after the third, pause the window. The lines past the first draw
over the battle panel's slots.
"""
    {
        sep #0x20
        lda #0x01
        sta.l panel_slots_overwritten
        rep #0x20
        lda.l battle_vwf_position

        cmp.w #0x1e << 3
        bpl line2
        lda.w #0x1e << 3
        bra end

line2:
        cmp.w #0x3c << 3
        bpl line3
        lda.w #0x3c << 3
        bra end

line3:
        lda.w #0x0000
        bra change_window
        bra end

change_window:
        sta.l battle_vwf_position
        sep #0x20
        jmp.l battle_vwf_window_pause
end:
        sta.l battle_vwf_position
        sep #0x20
        jmp.l battle_vwf_new_line_return
    }

battle_vwf_char:
"""Draw the char in $1E into the battle text buffer at the current pixel position."""
    {
        phb
        lda #0x7E
        pha
        plb

        lda 0x1e

        sta.l 0x004202
        lda #17
        sta.l 0x004203
        nop
        nop
        rep #0x20
        lda.l 0x004216
        tax

        lda.l battle_vwf_position
        pha
        and #0x3ff8
        asl
        asl
        tay
        pla
        and.w #0x0007
        sep #0x20
        bne shift_copy
        jmp.w raw_copy


shift_copy:
        phx
        tax
        lda.l shift_table, x
        plx
        sta.l 0x004202

        lda #0x10
        sta 0x08
        phx

shift_copy_loop:
        lda.l vwf_font, x
        sta.l 0x004203
        nop
        nop
        rep #0x20
        lda.l 0x004216
        sep #0x20
        sta.w 0x0020 + 0xD000, y
        xba
        ora.w 0x0000 + 0xD000, y
        sta.w 0x0000 + 0xD000, y
        inx
        iny
        iny

        dec 0x08
        bne shift_copy_loop
        plx
        jmp.w add_letter_length

raw_copy:
        lda.b #0x10
        sta 0x08
        phx
raw_copy_loop:
        lda.l vwf_font, x
        sta.w 0x0000 + 0xD000, y
        inx
        iny
        iny
        dec 0x08
        bne raw_copy_loop
        plx

add_letter_length:
        pha
        phx
; do the dma transfer before incrementing battle_dma_transfer
        jsr.l battle_dma_transfer
        plx
        pla
        lda.l vwf_font + 16, x
        plb

        rep #0x20
        and.w #0x00ff
        clc
        adc.l battle_vwf_position
        inc
        sta.l battle_vwf_position

        sep #0x20
        jmp.l return_from_battle_vwf_char

shift_table:
        .db 0
        .db 0x80
        .db 0x40
        .db 0x20
        .db 0x10
        .db 0x08
        .db 0x04
        .db 0x02
    }
}

.alloc battle_vwf_page in expansion {
battle_vwf_clear_window:
"""
Blank the three text lines, in the buffer and in VRAM, once the window pause is over. The engine's pause (C09B98)
scrolls the buffer up a line for its own text, which went on at the last line; the VWF starts the next page at the
top, where the scrolled line would show until the pen wrote over each of its columns.
"""
    {
        php
        phb
        rep #0x30
        lda.w #0x0000
        ldx.w #_LINE_BYTES * _LINES - 2
clear:
        sta.l _BUFFER, x
        dex
        dex
        bpl clear

        sep #0x20
        lda.b #0x00
        pha
        plb
        ldx.w #0x0000
upload:
        phx
        jsr.l wait_for_something__long  ; a line a frame, inside vblank
        plx
        lda.b #0x80
        sta 0x2115
        lda.b #0x01
        sta 0x4300
        lda.b #0x18
        sta 0x4301
        lda.b #_BUFFER >> 16
        sta 0x4304
        rep #0x20
        txa
        lsr
        clc
        adc.w #_VRAM
        sta 0x2116
        txa
        clc
        adc.w #_BUFFER & 0xFFFF
        sta 0x4302
        lda.w #_LINE_BYTES
        sta 0x4305
        sep #0x20
        lda.b #0x01
        sta 0x420B
        rep #0x20
        txa
        clc
        adc.w #_LINE_BYTES
        tax
        sep #0x20
        cpx.w #_LINE_BYTES * _LINES
        bne upload

        plb
        plp
        rtl
    }
}
