"""Variable-width font shared by the dialog, battle and load game renderers (assets/vwf.bin)."""

.include "src/ed_reloc.i"

.alloc vwf_font in ed_reloc {
    .incbin "assets/vwf.bin"
}
