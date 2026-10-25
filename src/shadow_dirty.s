"""
The menus' tilemap shadows (BG3 at 7EC400, BG2 at 7ED400, 4 KB each) go to VRAM only where they changed.

The engine queues a whole shadow every frame, BG3 on even frames and BG2 on odd ones: 4 KB a vblank, most of it
unchanged. Every writer of the shadows marks the bytes it wrote, after writing them, in a span per map; nmi_frame's
drain trims the engine's queue entries to the spans before it runs them. A map without a change still sends a
512-byte slice, round robin, so a writer missed here shows within eight of its frames.
"""

.include "src/expansion.i"
.include "src/sram_work.i"


SHADOW = 0x7EC400
BG2_SHADOW = 0x7ED400
MAP_BYTES = 0x1000
SHADOW_BYTES = 2 * MAP_BYTES
BG2_HALF = 0x800  ; the BG2 shadow's halves go to two VRAM maps
SWEEP = 0x200
SWEEP_MASK = MAP_BYTES / SWEEP - 1
TEXT_CURSOR = 0x001860
DMA_QUEUE_TAIL = 0x001A00
BG2_TARGET = 0x001868  ; nonzero: the BG2 shadow goes to the maps' other copy

; A queue entry: source address, its bank, VRAM word address, byte count, VMAIN.
ENTRY_SOURCE = 0
ENTRY_BANK = 2
ENTRY_VRAM = 3
ENTRY_SIZE = 5
ENTRY = 8

; Per map: the changed bytes lo-hi (offsets in the map, hi past the last; hi 0: none), the next sweep slice.
; bg2_entry: the queue entry of the BG2 shadow's first half (0: none queued). bg2_target: BG2_TARGET's last value.
; presents: bit 0 for a BG3 upload, bit 1 for a BG2 one, since the tests last cleared it.
.struct ShadowDirty {
    word bg3_lo
    word bg3_hi
    word bg2_lo
    word bg2_hi
    word bg3_sweep
    word bg2_sweep
    word bg2_entry
    word bg2_target
    word presents
}

.reserve shadow_dirty as ShadowDirty in sram_work

.macro marked_store(base) {
    """sta.l base, x, then mark the word it wrote; rtl. Keeps every register and P."""
    php
    sta.l base, x
    rep #0x30
    phy
    phx
    pha
    txa
    clc
    adc.w #( base - SHADOW ) & 0xFFFF
    tax
    clc
    adc.w #0x0002
    tay
    jsr.w _mark
    pla
    plx
    ply
    plp
    rtl
}

.macro store_site(site, helper) {
    """The engine's sta.l at site (4 bytes) becomes jsl helper, the same store marked."""
    .alloc at site {
        jsl.l helper
    }
}


; The engine's text primitives: sta.l 7EC3C0-7ED400, x, each now a call storing then marking.
store_site(0xEE4A6D, shadow_sta_c3c0)
store_site(0xEE4A7E, shadow_sta_c3c0)
store_site(0xEE4A97, shadow_sta_c3c0)
store_site(0xEE4AA4, shadow_sta_c3c0)
store_site(0xEE4CE6, shadow_sta_c3c0)
store_site(0xEE4D09, shadow_sta_c3c0)
store_site(0xEE4D61, shadow_sta_c3c0)
store_site(0xEE4D84, shadow_sta_c3c0)
store_site(0xEE4D9F, shadow_sta_c3c0)
store_site(0xEE4DC2, shadow_sta_c3c0)
store_site(0xEE4E65, shadow_sta_c3fa)
store_site(0xEE4ECA, shadow_sta_c3fa)
store_site(0xEE4F7D, shadow_sta_c3fa)
store_site(0xEE4E69, shadow_sta_c3fc)
store_site(0xEE4ED0, shadow_sta_c3fc)
store_site(0xEE4EE9, shadow_sta_c3fc)
store_site(0xEE4F83, shadow_sta_c3fc)
store_site(0xEE4F9C, shadow_sta_c3fc)
store_site(0xEEB4D4, shadow_sta_c3fc)
store_site(0xEEB51D, shadow_sta_c3fc)
store_site(0xEE4E43, shadow_sta_c3fe)
store_site(0xEE4E6D, shadow_sta_c3fe)
store_site(0xEE4ED6, shadow_sta_c3fe)
store_site(0xEE4EEF, shadow_sta_c3fe)
store_site(0xEE4F02, shadow_sta_c3fe)
store_site(0xEE4F89, shadow_sta_c3fe)
store_site(0xEE4FA2, shadow_sta_c3fe)
store_site(0xEE4FB5, shadow_sta_c3fe)
store_site(0xEEB4D0, shadow_sta_c3fe)
store_site(0xEEB519, shadow_sta_c3fe)
store_site(0xEE4A62, shadow_sta_c400)
store_site(0xEE4A77, shadow_sta_c400)
store_site(0xEE4A8C, shadow_sta_c400)
store_site(0xEE4AA0, shadow_sta_c400)
store_site(0xEE4CDB, shadow_sta_c400)
store_site(0xEE4CF0, shadow_sta_c400)
store_site(0xEE4CFE, shadow_sta_c400)
store_site(0xEE4D56, shadow_sta_c400)
store_site(0xEE4D6B, shadow_sta_c400)
store_site(0xEE4D79, shadow_sta_c400)
store_site(0xEE4DA3, shadow_sta_c400)
store_site(0xEE4DCF, shadow_sta_c400)
store_site(0xEE4E47, shadow_sta_c400)
store_site(0xEE4E71, shadow_sta_c400)
store_site(0xEE4EDC, shadow_sta_c400)
store_site(0xEE4EF5, shadow_sta_c400)
store_site(0xEE4F08, shadow_sta_c400)
store_site(0xEE4F15, shadow_sta_c400)
store_site(0xEE4F8F, shadow_sta_c400)
store_site(0xEE4FA8, shadow_sta_c400)
store_site(0xEE4FBB, shadow_sta_c400)
store_site(0xEE4FC8, shadow_sta_c400)
store_site(0xEE5026, shadow_sta_c400)
store_site(0xEE5062, shadow_sta_c400)
store_site(0xEE54EA, shadow_sta_c400)
store_site(0xEE5503, shadow_sta_c400)
store_site(0xEE6F3B, shadow_sta_c400)
store_site(0xEE909A, shadow_sta_c400)
store_site(0xEE90EC, shadow_sta_c400)
store_site(0xEE9123, shadow_sta_c400)
store_site(0xEEB4CC, shadow_sta_c400)
store_site(0xEEB515, shadow_sta_c400)
store_site(0xEE5035, shadow_sta_c402)
store_site(0xEE5045, shadow_sta_c402)
store_site(0xEE5071, shadow_sta_c402)
store_site(0xEE5081, shadow_sta_c402)
store_site(0xEE5095, shadow_sta_c440)
store_site(0xEE50B8, shadow_sta_c440)
store_site(0xEE6612, shadow_sta_d400)

; decompress_to (EE1D00), its end: ldy $06 / sty $03 (the destination back to its start) / pld / plb / plp / rtl.
.alloc at 0xEE1D41 {
    jml.l shadow_decompressed
}

; clear_menu_shadow's end, the BG3 shadow zeroed: ply / plx / pla / plb / plp / rtl.
.alloc at 0xEE50E4 {
    jml.l shadow_bg3_cleared
}

; clear_bg2_shadow's end: ply / plx / pla / plb / plp / rtl.
.alloc at 0xEE5104 {
    jml.l shadow_bg2_cleared
}

; clear_rect (EE4FD3, stz $C400,x a row at a time), its row loop: dec $02 / bne EE4FE7 / plb / plp / rtl.
.alloc at 0xEE4FFA {
    jml.l shadow_rect_cleared
}

; convert_2bpp_to_4bpp_80_tiles (into the BG2 shadow), its loop: dec $00 / bne EE865E / plp / rts.
.alloc at 0xEE86B2 {
    jml.l shadow_tiles_converted
}

; EE99B5's separator: sta $C400,x / ldx $12.
.alloc at 0xEE9A24 {
    jml.l shadow_separator
    nop
}

; the per-frame upload's BG2 half (EEFD73, odd frames): lda $1868 / bne EEFD9C, then two queue entries.
.alloc at 0xEEFD7E {
    jml.l shadow_bg2_queued
}

.alloc shadow_dirty_code in expansion {
shadow_sta_c3c0:
"""sta.l 7EC3C0, x, marked. Keeps every register and P."""
    marked_store(0x7EC3C0)

shadow_sta_c3fa:
"""sta.l 7EC3FA, x, marked. Keeps every register and P."""
    marked_store(0x7EC3FA)

shadow_sta_c3fc:
"""sta.l 7EC3FC, x, marked. Keeps every register and P."""
    marked_store(0x7EC3FC)

shadow_sta_c3fe:
"""sta.l 7EC3FE, x, marked. Keeps every register and P."""
    marked_store(0x7EC3FE)

shadow_sta_c400:
"""sta.l 7EC400, x, marked. Keeps every register and P."""
    marked_store(0x7EC400)

shadow_sta_c402:
"""sta.l 7EC402, x, marked. Keeps every register and P."""
    marked_store(0x7EC402)

shadow_sta_c440:
"""sta.l 7EC440, x, marked. Keeps every register and P."""
    marked_store(0x7EC440)

shadow_sta_d400:
"""sta.l 7ED400, x, marked. Keeps every register and P."""
    marked_store(0x7ED400)

shadow_dirty_range:
"""Mark shadow bytes X to Y (offsets from 7EC400, Y past the last; 16-bit, clamped to the shadows). Keeps all."""
    php
    rep #0x30
    pha
    phx
    phy
    jsr.w _mark
    ply
    plx
    pla
    plp
    rtl

shadow_dirty_bg3:
"""Mark the whole BG3 shadow. Keeps every register and P."""
    php
    rep #0x30
    pha
    phx
    phy
    ldx.w #0x0000
    ldy.w #MAP_BYTES
    jsr.w _mark
    ply
    plx
    pla
    plp
    rtl

shadow_dirty_bg2:
"""Mark the whole BG2 shadow. Keeps every register and P."""
    php
    rep #0x30
    pha
    phx
    phy
    jsr.w _mark_bg2
    ply
    plx
    pla
    plp
    rtl

_mark_bg2:
    ldx.w #MAP_BYTES
    ldy.w #SHADOW_BYTES
    jmp.w _mark

_mark:
"""
Mark shadow bytes X to Y (16-bit offsets from 7EC400; one from 0x8000 up lies before the shadows). Each span's low
bound is stored before its high one: an NMI taking the span between them still leaves these bytes marked. 16-bit;
clobbers A, X and Y.
"""
    txa
    jsr.w _clamp
    tax
    tya
    jsr.w _clamp
    tay
    cpx.w #MAP_BYTES
    bcs _bg2_part
    tya
    cmp.w #MAP_BYTES
    bcc _bg3_end
    lda.w #MAP_BYTES
_bg3_end:
    phy
    tay
    jsr.w _merge_bg3
    ply
_bg2_part:
    cpy.w #MAP_BYTES + 1
    bcc _marked
    tya
    sec
    sbc.w #MAP_BYTES
    tay
    txa
    sec
    sbc.w #MAP_BYTES
    bcs _bg2_start
    lda.w #0x0000
_bg2_start:
    tax
    jsr.w _merge_bg2
_marked:
    rts

_merge_bg3:
"""BG3's span with X to Y; nothing when Y is not past X."""
    tya
    dec
    phx
    cmp 0x01, s
    plx
    bcc _bg3_merged
    lda.l shadow_dirty.bg3_hi
    beq _bg3_new
    txa
    cmp.l shadow_dirty.bg3_lo
    bcs _bg3_keep_lo
    sta.l shadow_dirty.bg3_lo
_bg3_keep_lo:
    tya
    cmp.l shadow_dirty.bg3_hi
    bcc _bg3_merged
    sta.l shadow_dirty.bg3_hi
_bg3_merged:
    rts
_bg3_new:
    txa
    sta.l shadow_dirty.bg3_lo
    tya
    sta.l shadow_dirty.bg3_hi
    rts

_merge_bg2:
"""BG2's span with X to Y; nothing when Y is not past X."""
    tya
    dec
    phx
    cmp 0x01, s
    plx
    bcc _bg2_merged
    lda.l shadow_dirty.bg2_hi
    beq _bg2_new
    txa
    cmp.l shadow_dirty.bg2_lo
    bcs _bg2_keep_lo
    sta.l shadow_dirty.bg2_lo
_bg2_keep_lo:
    tya
    cmp.l shadow_dirty.bg2_hi
    bcc _bg2_merged
    sta.l shadow_dirty.bg2_hi
_bg2_merged:
    rts
_bg2_new:
    txa
    sta.l shadow_dirty.bg2_lo
    tya
    sta.l shadow_dirty.bg2_hi
    rts

_clamp:
"""Offset A (16-bit) into 0-SHADOW_BYTES: 0 from 0x8000 up (before the shadows), SHADOW_BYTES past them."""
    cmp.w #0x8000
    bcs _before
    cmp.w #SHADOW_BYTES
    bcc _clamped
    lda.w #SHADOW_BYTES
_clamped:
    rts
_before:
    lda.w #0x0000
    rts

shadow_decompressed:
"""decompress_to's end, 8-bit A: mark what it wrote, $06 (its start) to $03, when that is bank 7E."""
    php
    rep #0x30
    pha
    phx
    phy
    lda.b 0x04
    and.w #0xFF00
    cmp.w #0x7E00
    bne _not_shadow
    lda.b 0x06
    sec
    sbc.w #SHADOW & 0xFFFF
    tax
    lda.b 0x03
    sec
    sbc.w #SHADOW & 0xFFFF
    tay
    jsr.w _mark
_not_shadow:
    ply
    plx
    pla
    plp
    ldy.b 0x06
    sty.b 0x03
    jml 0xEE1D45

shadow_bg3_cleared:
"""clear_menu_shadow's end: mark the BG3 shadow, then its pulls."""
    jsl.l shadow_dirty_bg3
    ply
    plx
    pla
    plb
    jml 0xEE50E8

shadow_bg2_cleared:
"""clear_bg2_shadow's end: mark the BG2 shadow, then its pulls."""
    jsl.l shadow_dirty_bg2
    ply
    plx
    pla
    plb
    jml 0xEE5108

shadow_rect_cleared:
"""clear_rect's row loop; at its end X is the row past the last: mark the cursor to it."""
    dec.b 0x02
    beq _rect_done
    jml 0xEE4FE7
_rect_done:
    php
    rep #0x30
    pha
    phx
    phy
    txa
    tay
    lda.l TEXT_CURSOR
    tax
    jsr.w _mark
    ply
    plx
    pla
    plp
    jml 0xEE4FFE

shadow_tiles_converted:
"""convert_2bpp_to_4bpp_80_tiles's loop; at its end the BG2 shadow holds the tiles: mark it."""
    dec.b 0x00
    beq _converted
    jml 0xEE865E
_converted:
    jsl.l shadow_dirty_bg2
    jml 0xEE86B6

shadow_separator:
"""EE99B5's separator, 16-bit A, DB 7E: the store, marked, then ldx $12."""
    sta.l SHADOW, x
    php
    rep #0x30
    pha
    phx
    phy
    txa
    tay
    iny
    iny
    jsr.w _mark
    ply
    plx
    pla
    plp
    ldx.b 0x12
    jml 0xEE9A29

shadow_bg2_queued:
"""
The per-frame upload's BG2 half, 16-bit A: note the queue entry its two take, for shadow_trim_bg2; the whole shadow
changes when its target copy does. Leaves A and the flags as lda $1868.
"""
    lda.l DMA_QUEUE_TAIL
    sta.l shadow_dirty.bg2_entry
    lda.l BG2_TARGET
    cmp.l shadow_dirty.bg2_target
    beq _same_target
    sta.l shadow_dirty.bg2_target
    jsl.l shadow_dirty_bg2
_same_target:
    lda.l BG2_TARGET
    jml 0xEEFD82

shadow_trim_bg3:
"""
nmi_frame's drain, before the engine's queue runs: queue entry X (the BG3 shadow's, whole) down to the changed
bytes, or the next sweep slice. 16-bit X; keeps all.
"""
    php
    rep #0x30
    pha
    phx
    phy
    lda.l shadow_dirty.bg3_hi
    beq _bg3_sweep
    tay
    lda.w #0x0000
    sta.l shadow_dirty.bg3_hi
    lda.l shadow_dirty.bg3_lo
    bra _bg3_span
_bg3_sweep:
    lda.l shadow_dirty.bg3_sweep
    inc
    and.w #SWEEP_MASK
    sta.l shadow_dirty.bg3_sweep
    xba
    asl  ; * SWEEP
    pha
    clc
    adc.w #SWEEP
    tay
    pla
_bg3_span:
    jsr.w _span_bytes
    bcs _bg3_whole
    sta.l 0x000000 + ENTRY_SIZE, x
    tya
    pha
    clc
    adc.w #SHADOW & 0xFFFF
    sta.l 0x000000 + ENTRY_SOURCE, x
    pla
    lsr
    clc
    adc.l 0x000000 + ENTRY_VRAM, x
    sta.l 0x000000 + ENTRY_VRAM, x
_bg3_whole:
    lda.l shadow_dirty.presents
    ora.w #0x0001
    sta.l shadow_dirty.presents
    ply
    plx
    pla
    plp
    rtl

shadow_take_bg3:
"""
The BG3 span, for an upload outside the engine's queue: A its start, Y its length (0: nothing changed), the span
cleared; torn, the whole map. 16-bit A, X and Y; keeps X.
"""
    lda.l shadow_dirty.bg3_hi
    beq _nothing_taken
    tay
    lda.w #0x0000
    sta.l shadow_dirty.bg3_hi
    lda.l shadow_dirty.bg3_lo
    jsr.w _span_bytes
    bcc _span_taken
    ldy.w #0x0000
    lda.w #MAP_BYTES
_span_taken:
    pha
    tya
    ply
    rtl
_nothing_taken:
    tay
    rtl

_span_bytes:
"""
Span A to Y (Y past the last, both in a map) to even bounds: Y its start, A its length, carry clear; carry set when
torn (an NMI between a mark's two stores), the whole map then going. The NMI's: no direct page.
"""
    and.w #0xFFFE
    pha
    tya
    inc
    and.w #0xFFFE
    sec
    sbc 0x01, s
    beq _torn
    bcc _torn
    ply
    clc
    rts
_torn:
    ply
    sec
    rts

shadow_trim_bg2:
"""
nmi_frame's drain, before the engine's queue runs: the BG2 shadow's two entries, when queued, down to the changed
bytes or the next sweep slice, each half its own. Keeps all.
"""
    php
    rep #0x30
    pha
    phx
    phy
    lda.l shadow_dirty.bg2_entry
    beq _bg2_none
    tax
    lda.w #0x0000
    sta.l shadow_dirty.bg2_entry
    jsr.w _is_bg2_map
    bcc _bg2_none
    lda.l shadow_dirty.bg2_hi
    beq _bg2_sweep
    tay
    lda.w #0x0000
    sta.l shadow_dirty.bg2_hi
    lda.l shadow_dirty.bg2_lo
    bra _bg2_span
_bg2_sweep:
    lda.l shadow_dirty.bg2_sweep
    inc
    and.w #SWEEP_MASK
    sta.l shadow_dirty.bg2_sweep
    xba
    asl  ; * SWEEP
    pha
    clc
    adc.w #SWEEP
    tay
    pla
_bg2_span:
    jsr.w _span_bytes
    bcs _bg2_whole
    jsr.w _trim_halves
_bg2_whole:
    lda.l shadow_dirty.presents
    ora.w #0x0002
    sta.l shadow_dirty.presents
_bg2_none:
    ply
    plx
    pla
    plp
    rtl

_is_bg2_map:
"""Carry set when queue entry X and the next upload the BG2 shadow's halves, in order."""
    txa
    clc
    adc.w #2 * ENTRY
    cmp.l DMA_QUEUE_TAIL
    beq _bg2_fits
    bcs _not_bg2_map
_bg2_fits:
    lda.l 0x000000 + ENTRY_SOURCE, x
    cmp.w #BG2_SHADOW & 0xFFFF
    bne _not_bg2_map
    lda.l 0x000000 + ENTRY + ENTRY_SOURCE, x
    cmp.w #( BG2_SHADOW + BG2_HALF ) & 0xFFFF
    bne _not_bg2_map
    sec
    rts
_not_bg2_map:
    clc
    rts

_trim_halves:
"""BG2 entries X (first half) and X + ENTRY (second) to the bytes Y on, A long, of the BG2 shadow. No direct page."""
    phy  ; 0x03, s: the span's start
    pha
    tya
    clc
    adc 0x01, s
    sta 0x01, s  ; 0x01, s: its end
    lda 0x03, s
    cmp.w #BG2_HALF
    bcs _first_empty
    lda 0x01, s
    cmp.w #BG2_HALF
    bcc _first_end
    lda.w #BG2_HALF
_first_end:
    sec
    sbc 0x03, s
    pha
    lda 0x05, s
    tay
    pla
    jsr.w _trim_entry
    bra _second
_first_empty:
    lda.w #0x0000
    sta.l 0x000000 + ENTRY_SIZE, x
_second:
    txa
    clc
    adc.w #ENTRY
    tax
    lda 0x01, s
    cmp.w #BG2_HALF + 1
    bcc _second_empty
    sec
    sbc.w #BG2_HALF
    sta 0x01, s
    lda 0x03, s
    sec
    sbc.w #BG2_HALF
    bcs _second_start
    lda.w #0x0000
_second_start:
    sta 0x03, s
    lda 0x01, s
    sec
    sbc 0x03, s
    pha
    lda 0x05, s
    tay
    pla
    jsr.w _trim_entry
    bra _halves_done
_second_empty:
    lda.w #0x0000
    sta.l 0x000000 + ENTRY_SIZE, x
_halves_done:
    pla
    ply
    rts

_trim_entry:
"""Queue entry X to Y bytes in, A bytes long (A not 0): its source and VRAM address move on, its size is A."""
    sta.l 0x000000 + ENTRY_SIZE, x
    tya
    clc
    adc.l 0x000000 + ENTRY_SOURCE, x
    sta.l 0x000000 + ENTRY_SOURCE, x
    tya
    lsr
    clc
    adc.l 0x000000 + ENTRY_VRAM, x
    sta.l 0x000000 + ENTRY_VRAM, x
    rts
}
