"""
Console WRAM, as a bss pool: every variable the patch keeps in RAM is reserved here, so the linker checks them
against each other.

Reservations are pinned where the patch has always kept them. battle_vwf_position (7EBE00) shares its word with
the field room-event table at 7EB800-7EC3FF (bank DA). The battle owns it: going into a battle the game zeroes
7EA000-7EBFFF (C04A44), and in kintsuki traces of scenario 00's battle, vanilla and patched, nothing else writes it
while battle text draws.
"""


.pool wram {
    bss
    range 0x7E0000 0x7EFFFF
    range 0x7F0000 0x7FFFFF
    strategy pack
}
