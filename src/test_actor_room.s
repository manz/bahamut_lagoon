; Test room for unknown actor opcodes
; Tests hypotheses for 0x16, 0x47, and other actor-related opcodes

.include 'src/room_macros.s'
.table './text/table/fr.tbl'

; Room header
room_start:
    .dw main_entry     ; Entry point
    .dw actors_table   ; Actors table
    .dw 0x0000         ; Room 4 (unused)
    .dw 0x0000         ; Player events (unused)  
    .dw 0x0000         ; Room 8 (unused)
    .dw 0x0000         ; Room A (unused)

; Main room logic
main_entry:
    ; Set up scene
    setup_scene_background(0x15)
    setup_scene_mask(0x00, 0x00)
    
    ; Fade in
    set_screen_status(0x01)
    animate_brightness(0x00, 0x0F, 0x20, 0x00)
    pause(0x20)
    
    ; Show first actor
    actor_show(0x5, 0x8, 0x12)
    actor_playable(0x5)
    
    ; Test actor state and facing sequence (common pattern)
    actor_state(0x5, 0x0D)
    .db 0x47, 0x05                    ; Test 0x47 - actor enable/visibility
    .db 0x16, 0x05, 0x01              ; Test 0x16 - actor facing direction
    
    ; Show dialog about what we're testing
    set_window_position(0x02, 0x06)
    set_window_style(0x01)
    display_text(test_text)
    close_window()
    
    ; Test different actor facing directions
    pause(0x30)
    
    ; Face different directions
    .db 0x16, 0x05, 0x00              ; Try facing direction 0
    pause(0x20)
    .db 0x16, 0x05, 0x02              ; Try facing direction 2  
    pause(0x20)
    .db 0x16, 0x05, 0x03              ; Try facing direction 3
    pause(0x20)
    .db 0x16, 0x05, 0x01              ; Back to direction 1
    
    ; Test with second actor
    actor_show(0x6, 0x10, 0x12)
    actor_state(0x6, 0x0D)
    .db 0x47, 0x06                    ; Enable actor 6
    .db 0x16, 0x06, 0x01              ; Set facing for actor 6
    
    ; Test movement with facing
    actor_move(0x5, 0x30, 0xFF)       ; Move actor 5 right
    wait_for_actor_to_be_still(0x5)
    .db 0x16, 0x05, 0x03              ; Face right after moving
    
    ; Test sound effect hypothesis for 0x6D
    .db 0x6D, 0xCC                    ; Common 0x6D pattern - test if sound plays
    pause(0x10)
    .db 0x6D, 0x1D                    ; Different sound ID
    pause(0x10)
    
    ; Test action trigger 0x38 before dialog
    .db 0x38                          ; Action trigger - no params
    set_window_style(0x01)
    display_text(test_text2)
    close_window()
    
    ; Test visual effect 0x24
    .db 0x24, 0x05, 0x10, 0xF5, 0x00  ; Common 0x24 pattern
    pause(0x20)
    
    ; Show final message
    set_window_position(0x02, 0x06) 
    set_window_style(0x01)
    display_text(end_text)
    close_window()
    
    ; Wait then fade out and exit
    pause(0x60)
    animate_brightness(0x0F, 0x00, 0x20, 0x00)
    pause(0x20)
    set_screen_status(0x00)
    exit()

; Actors table (minimal setup)
actors_table:
    ; Actor 5 data (player character)
    .db 0x05, 0xFF, 0x80, 0x80, 0x02, 0x08, 0x00
    ; Actor 6 data (companion)  
    .db 0x06, 0xFF, 0x80, 0x80, 0x02, 0x08, 0x00
    ; End marker
    .dw 0xFFFF

; Text data
test_text:
    .text 'Testing actor opcodes...'
    .text 'Actor facing and visibility.'
    .db 0xFF

test_text2:
    .text 'Action trigger test!'
    .text 'Did 0x38 work?'
    .db 0xFF
    
end_text:
    .text 'Test complete!'
    .text 'Observe actor behavior.'
    .db 0xFF