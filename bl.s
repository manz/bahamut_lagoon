
.include 'src/dialog_vwf.s'
.include 'src/battle_vwf.s'
.include 'src/dragon_feed.s'

*=0xed0000
    .incbin 'assets/vwf.bin'
    .include 'src/dialog_vwf_reloc.s'
    .include 'src/battle_vwf_reloc.s'
