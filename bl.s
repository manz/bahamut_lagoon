
.include 'src/dialog_vwf.s'
.include 'src/battle_vwf.s'
.include 'src/dragon_feed.s'

.include 'src/battle.s'
.include 'src/naming_screen.s'
.include 'src/draw_inline_string.s'
; copy font from rom instead of ram (2bpp) the 4bpp version is derived from the 2bpp decompressed in ram
; TODO: write a compressor and properly replace the asset.
*=0xEE8519
    .dw src_assets_ee0020_bin & 0xffff
    .db src_assets_ee0020_bin >> 16


; reclaim japansese characters space for code
*=0xed0000
    .incbin 'assets/vwf.bin'
    .include 'src/dialog_vwf_reloc.s'
    .include 'src/battle_vwf_reloc.s'
    .incbin 'src_assets/ee0020.bin'
