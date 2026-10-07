"""
Test room for opcode testing: displays text and exits.

Built with build_room.py, not part of the patch.
"""


.include "src/room_macros.s"
.table "./text/table/fr.tbl"
; Room header

room_start:
"""Room header: pointers to the entry point and the actors table."""
    .dw main_entry  ; Entry point
    .dw actors_table  ; Actors table
    .dw 0x0000  ; Room 4 (unused)
    .dw 0x0000  ; Player events (unused)
    .dw 0x0000  ; Room 8 (unused)
    .dw 0x0000  ; Room A (unused)

; Main room logic

main_entry:
"""Room entry point: the script the interpreter runs."""
    ; Set up scene
    load_map(0x15)
    set_camera(0x00, 0x00)

; Fade in
    set_screen(0x01)
    fade_brightness(0x00, 0x0F, 0x20, 0x00)
    wait_frames(0x20)

; Show test text
    set_window_position(0x0A, 0x06)
    open_window(0x01)
    display_text(test_text)
    close_window()

; Wait a bit
    wait_frames(0x60)

; Fade out and exit
    fade_brightness(0x0F, 0x00, 0x20, 0x00)
    wait_frames(0x20)
    set_screen(0x00)
    exit()

; Actors table (empty for test)

actors_table:
"""Actors placed in the room."""
    .dw 0xFFFF

; Text data

test_text:
"""Text shown by the test script."""
    .text "Hello from a816 room!"
    .db 0xFF
