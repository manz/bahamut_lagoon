"""
Item and spell descriptions (feed menu, item menus, the combat scene's spell menu): their readers in bank C1 had the
messages' bank hardcoded.

The descriptions are entries of the messages table (pointers at EE35F1), which build.py relocates to bank FD and
repoints in the three vanilla readers it knows (EE5404, EE553A, C0D8AD). These readers, at C14305 (items, through
EE3020) and C1434D (spells, through EE3022), load bank EE as a constant for both the pointer table ($2A) and the
strings ($60), so they read the relocated offsets in bank EE: the spell menu showed code bytes as text.
"""


.include "src/expansion.i"

MESSAGES_BANK = 0xEE5405  ; operand of the messages loop's `lda #bank`, which build.py sets to the messages' bank

.alloc item_description_banks in expansion {
set_item_description_banks:
"""The pointer table stays in bank EE; the strings are where build.py put the messages. Leaves A 8-bit."""
    sep #0x20
    lda #0xEE
    sta 0x2A
    lda.l MESSAGES_BANK
    sta 0x60
    rtl
}

.alloc at 0xC14311 {
    jsr.l set_item_description_banks
    nop
    nop
    nop
    nop
}

.alloc at 0xC14355 {
    jsr.l set_item_description_banks
    nop
    nop
    nop
    nop
}
