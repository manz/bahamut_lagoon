"""
Bank ED pool for the relocated variable-width font code and its font.

Bounded to the bytes the patch already overwrites (vanilla ED0000-ED144C). The vanilla battle messages at
ED2000-ED35F0 are relocated to bank FD by build.py and are the next free run, once the gap between is confirmed
unused.
"""


.pool ed_reloc {
    range 0xED0000 0xED144C
    strategy order
}
