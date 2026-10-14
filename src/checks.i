"""
Checks: asserts the patch runs where it is about to spoil the screen, in builds with CHECKS (build.py --checks, and
the debug build). A failed check executes STP with its signature in A, the other registers as the write had them:
kintsuki, the tests and betaplayer's hunt report a stopped CPU with its registers and call stack, the write that
broke the window on top.
"""

; c1_vwf: a C1 window's frame cell (tiles 0x01-0x03, any flip) is about to take a VWF slot, a blank or an icon: the
; string's field, laid out by the engine for the Japanese text, runs over the window's border. X: the cell's offset.
CHECK_C1_FRAME = 0xC1F0

; battle_panel_vwf: a window or panel frame cell (codes 0xE0-0xE2, attribute 0x22 or 0x23) is about to take a
; character that is not a frame: a line's field runs over its window's border. A's low byte is lost to the
; signature; Y: the tilemap cell, X: past the character in the line.
CHECK_PANEL_FRAME = 0xC0F0
