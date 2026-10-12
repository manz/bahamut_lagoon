"""
The layout of build.py's generated long_names.s (utils/name_tables.py), which small_vwf reads.
"""

; A full-names table: long_name_tables lists one per 8-byte name table, a 0 record ends it.
.struct LongNameTable {
    long record  ; the bus address of record 0's name
    word count
    word pointers  ; a word per name, to its full name
    byte record_size
    word baked  ; a BakedEntry per name
}

; A string's baked tiles in small_vwf_baked_tiles.
.struct BakedEntry {
    word offset
    byte cells
    byte unused
}

; A static string of bank FD, by address: small_vwf_static_entries, small_vwf_static_baked words of them.
.struct StaticBaked {
    word address  ; its low word
    byte length
    byte unused
    BakedEntry baked
}
