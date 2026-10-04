.include "src/dialog_vwf.s"
.include "src/battle_vwf.s"
.include "src/dragon_feed.s"

.include "src/battle.s"

.include "src/title_screen.s"
;.include 'src/naming_screen.s'
.include "src/load_game.s"
.include "src/draw_inline_string.s"
.include "src/vm.s"


DEBUG := 0
VRAM_128k := 0
.if DEBUG {
; enable debug mode
    *=0xc0ffad
    .dw 0x0000
    *=0xc0ffae
    .dw 0x00ff
}

.if VRAM_128k {
    /*
; Enables 128k vram to see if it works
; it looks like DMA transfers and Background addresses are computed correctly
; da01c6 lda #$ff                A:80e0 X:0000 Y:0000 S:1fef D:0000 DB:00 NvMxdizc V:236 H:166 F:24
    */


    *=0xda01c6
    lda.b #0xfe

; clear vram
    *=0xda02c2
    ldx.w #0xffff
}

*=0xe61b40
.incbin "src_assets/8x8_battle.dat"

*=0xc8a000
.incbin "src_assets/8x8_font.dat"  ; reclaim japansese characters space for code

*=0xed0000
.incbin "assets/vwf.bin"
.include "src/dialog_vwf_reloc.s"
.include "src/battle_vwf_reloc.s"
.include "src/load_game_reloc.s"

end_of_code:

;*=0xC0FFD5					; Edit Internal ROM Header
;  .db 0x23					; ROM Mapper: SA1ROM
;.db 0x35					; Cart Contents: ROM + BW-RAM(RAM + SRAM) + SA-1

;*=0xC0FFD8					; Set BW-RAM Size
;  .db 0x07					; Setting BW-RAM size to 128 kB.

