"""Bahamut Lagoon French translation patch: hooks, relocated code and fonts."""

.import "dialog_vwf"
.import "battle_vwf"
.import "dragon_feed"
.import "battle"
.import "title_screen"
;.import "naming_screen"
.import "load_game"
.import "draw_inline_string"
.import "vm"
.import "vwf_font"
.import "dialog_vwf_reloc"
.import "battle_vwf_reloc"
.import "load_game_reloc"


VRAM_128K := 0
.if DEBUG {
; enable debug mode
    .alloc at 0xc0ffad {
    .db 0x00, 0xff
    }
}

.if VRAM_128K {
    /*
; Enables 128k vram to see if it works
; it looks like DMA transfers and Background addresses are computed correctly
; da01c6 lda #$ff                A:80e0 X:0000 Y:0000 S:1fef D:0000 DB:00 NvMxdizc V:236 H:166 F:24
    */


    .alloc at 0xda01c6 {
    lda.b #0xfe

; clear vram
    }
    .alloc at 0xda02c2 {
    ldx #0xffff
    }
}

.alloc at 0xe61b40 {
    .incbin "src_assets/8x8_battle.dat"
}

.alloc at 0xc8a000 {
    .incbin "src_assets/8x8_font.dat"  ; reclaim japanese characters space for code
}


;*=0xC0FFD5					; Edit Internal ROM Header
;  .db 0x23					; ROM Mapper: SA1ROM
;.db 0x35					; Cart Contents: ROM + BW-RAM(RAM + SRAM) + SA-1

;*=0xC0FFD8					; Set BW-RAM Size
;  .db 0x07					; Setting BW-RAM size to 128 kB.
