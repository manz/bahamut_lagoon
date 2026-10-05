"""
Console WRAM, as a bss pool: every variable the patch keeps in RAM is reserved here, so the linker checks them
against each other.

Reservations are pinned where the patch has always kept them. battle_vwf_position (7EBE00) sits inside a table
the game clears and updates at 7EB800-7EC3FF (bank DA room code writes it in the field); whether that collides
during battles is unverified until a battle can be reached in the kintsuki tests.
"""


.pool wram {
    bss
    range 0x7E0000 0x7EFFFF
    range 0x7F0000 0x7FFFFF
    strategy pack
}
