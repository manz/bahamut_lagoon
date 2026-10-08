"""
Test room for unknown actor opcodes (0x16, 0x47 and other actor-related ones).

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

; Show first actor
    actor_place(0x5, 0x8, 0x12)
    set_player_actor(0x5)

; Test actor state and facing sequence (common pattern)
    actor_set_frame(0x5, 0x0D)
    .db 0x47, 0x05  ; Test 0x47 - actor enable/visibility
    .db 0x16, 0x05, 0x01  ; Test 0x16 - actor facing direction

; Show dialog about what we're testing
    set_window_position(0x02, 0x06)
    open_window(0x01)
    display_text(test_text)
    close_window()

; Test different actor facing directions
    wait_frames(0x30)

; Face different directions
    .db 0x16, 0x05, 0x00  ; Try facing direction 0
    wait_frames(0x20)
    .db 0x16, 0x05, 0x02  ; Try facing direction 2
    wait_frames(0x20)
    .db 0x16, 0x05, 0x03  ; Try facing direction 3
    wait_frames(0x20)
    .db 0x16, 0x05, 0x01  ; Back to direction 1

; Test with second actor
    actor_place(0x6, 0x10, 0x12)
    actor_set_frame(0x6, 0x0D)
    .db 0x47, 0x06  ; Enable actor 6
    .db 0x16, 0x06, 0x01  ; Set facing for actor 6

; Test movement with facing
    actor_move(0x5, 0x30, 0xFF)  ; Move actor 5 right
    wait_actor_move(0x5)
    .db 0x16, 0x05, 0x03  ; Face right after moving

; Test sound effect hypothesis for 0x6D
    .db 0x6D, 0xCC  ; Common 0x6D pattern - test if sound plays
    wait_frames(0x10)
    .db 0x6D, 0x1D  ; Different sound ID
    wait_frames(0x10)

; Test action trigger 0x38 before dialog
    .db 0x38  ; Action trigger - no params
    open_window(0x01)
    display_text(test_text2)
    close_window()

; Test visual effect 0x24
    .db 0x24, 0x05, 0x10, 0xF5, 0x00  ; Common 0x24 pattern
    wait_frames(0x20)

; Show final message
    set_window_position(0x02, 0x06)
    open_window(0x01)
    display_text(end_text)
    close_window()

; Wait then fade out and exit
    wait_frames(0x60)
    fade_brightness(0x0F, 0x00, 0x20, 0x00)
    wait_frames(0x20)
    set_screen(0x00)
    exit()

; Actors table (minimal setup)

actors_table:
"""Actors placed in the room."""
    ; Actor 5 data (player character)
    .db 0x05, 0xFF, 0x80, 0x80, 0x02, 0x08, 0x00
    ; Actor 6 data (companion)
    .db 0x06, 0xFF, 0x80, 0x80, 0x02, 0x08, 0x00
    ; End marker
    .dw 0xFFFF

; Text data

test_text:
"""Text shown by the test script."""
    .text "Testing actor opcodes..."
    .text "Actor facing and visibility."
    .db 0xFF

test_text2:
"""Second text shown by the test script."""
    .text "Action trigger test!"
    .text "Did 0x38 work?"
    .db 0xFF

end_text:
"""Text shown before the room exits."""
    .text "Test complete!"
    .text "Observe actor behavior."
    .db 0xFF
