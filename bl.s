
.include 'src/dialog_vwf.s'
.include 'src/battle_vwf.s'
.include 'src/dragon_feed.s'

.include 'src/battle.s'

.include 'src/title_screen.s'
.include 'src/naming_screen.s'
.include 'src/draw_inline_string.s'


*=0xe61b40
    .incbin 'src_assets/8x8_battle.dat'

*=0xc8a000
    .incbin 'src_assets/8x8_font.dat'


; reclaim japansese characters space for code
*=0xed0000
    .incbin 'assets/vwf.bin'
    .include 'src/dialog_vwf_reloc.s'
    .include 'src/battle_vwf_reloc.s'
