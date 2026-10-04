; Test room for opcode testing
; Simple room that displays text and exits

.include 'src/room_macros.s'
.table './text/table/fr.tbl'
; Room header
room_start:
    .dw main_entry     ; Entry point
    .dw actors_table   ; Actors table
    .dw 0x0000          ; Room 4 (unused)
    .dw 0x0000          ; Player events (unused)  
    .dw 0x0000          ; Room 8 (unused)
    .dw 0x0000          ; Room A (unused)

; Main room logic
main_entry:
    ; Set up scene
    setup_scene_background(0x15)
    setup_scene_mask(0x00, 0x00)
    
    ; Fade in
    set_screen_status(0x01)
    animate_brightness(0x00, 0x0F, 0x20, 0x00)
    pause(0x20)
    
    ; Show test text
    set_window_position(0x0A, 0x06)
    set_window_style(0x01)
    display_text(test_text)
    close_window()
    
    ; Wait a bit
    pause(0x60)
    
    ; Fade out and exit
    animate_brightness(0x0F, 0x00, 0x20, 0x00)
    pause(0x20)
    set_screen_status(0x00)
    exit()

; Actors table (empty for test)
actors_table:
    .dw 0xFFFF

; Text data
test_text:
    .text 'Hello from a816 room!'
    .db 0xFF
