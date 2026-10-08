"""
The party status screen (X on the battle map): four units of four rows, packed by an HDMA table on BG3's vertical
scroll (EEB1C7, channel 7) that adds 4 to the scroll every row of text.

The table's last entry steps back from 0x46 to 0x44, so the line after the last row repeats the line two above it:
a stray line of pixels under SP/MP and Mag. A bug of the original game; the scroll now stays at 0x46.
"""

.alloc at 0xEEB1FB {
    .dw 0x0046  ; was 0x0044: the scroll from line 218 on
}
