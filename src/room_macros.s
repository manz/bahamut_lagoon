; Bahamut Lagoon Room Script Macro Library
; Generated automatically from opcodes_map.py
; Use with a816 assembler

; 0x00: jump
.macro jump(address) {
    .db 0x00
    .dw address
}

; 0x01: conditional_jump_1
.macro conditional_jump_1(param1, param2) {
    .db 0x01, param1, param2
}

; 0x02: conditional_jump_2
.macro conditional_jump_2(param1, param2) {
    .db 0x02, param1, param2
}

; 0x03: conditional_subroutine
.macro conditional_subroutine(param1, param2) {
    .db 0x03, param1, param2
}

; 0x04: conditional_jump_4
.macro conditional_jump_4(param1, param2) {
    .db 0x04, param1, param2
}

; 0x05: jump_to_subroutine
.macro jump_to_subroutine(address) {
    .db 0x05
    .dw address
}

; 0x06: return_from_subroutine
.macro return_from_subroutine() {
    .db 0x06
}

; 0x08: yes_no
.macro yes_no(text_addr, yes_addr, no_addr) {
    .db 0x08
    .dw text_addr
    .dw yes_addr
    .dw no_addr
}

; 0x09: multiple_choice
.macro multiple_choice(text_addr, choice1, choice2, choice3, choice4) {
    .db 0x09
    .dw text_addr
    .dw choice1
    .dw choice2
    .dw choice3
    .dw choice4
}

; 0x0C: set_state_bits
.macro set_state_bits() {
    .db 0x0C
}

; 0x0D: clear_state_bits
.macro clear_state_bits() {
    .db 0x0D
}

; 0x0E: actor_state
.macro actor_state(param1, param2) {
    .db 0x0E, param1, param2
}

; 0x0F: actor_speed
.macro actor_speed(param1, param2) {
    .db 0x0F, param1, param2
}

; 0x10: actor_stuff_10?
.macro actor_stuff_10(param1, param2) {
    .db 0x10, param1, param2
}

; 0x11: actor_playable
.macro actor_playable(param1) {
    .db 0x11, param1
}

; 0x12: actor_show
.macro actor_show(param1, param2, param3) {
    .db 0x12, param1, param2, param3
}

; 0x13: actor_move
.macro actor_move() {
    .db 0x13
}

; 0x1B: setup_scene_background
.macro setup_scene_background(param1) {
    .db 0x1B, param1
}

; 0x1C: setup_scene_mask
.macro setup_scene_mask(param1, param2) {
    .db 0x1C, param1, param2
}

; 0x27: center_scene_on_background?
.macro center_scene_on_background(param1, param2) {
    .db 0x27, param1, param2
}

; 0x29: set_screen_status
.macro set_screen_status(param1) {
    .db 0x29, param1
}

; 0x2A: animate_brightness
.macro animate_brightness(param1, param2, param3, param4) {
    .db 0x2A, param1, param2, param3, param4
}

; 0x34: set_window_position
.macro set_window_position(param1, param2) {
    .db 0x34, param1, param2
}

; 0x35: set_window_style
.macro set_window_style(param1) {
    .db 0x35, param1
}

; 0x36: close_window
.macro close_window() {
    .db 0x36
}

; 0x37: display_text
.macro display_text(text_address) {
    .db 0x37
    .dw text_address
}

; 0x3F: pause
.macro pause(param1) {
    .db 0x3F, param1
}

; 0x42: player_control_flag
.macro player_control_flag(param1) {
    .db 0x42, param1
}

; 0x43: change_room
.macro change_room(param1) {
    .db 0x43, param1
}

; 0x44: init state
.macro init_state(param1, param2, param3, param4) {
    .db 0x44, param1, param2, param3, param4
}

; 0x48: wait_for_actor_to_be_still
.macro wait_for_actor_to_be_still(param1) {
    .db 0x48, param1
}

; 0x5A: show_mode7_animation
.macro show_mode7_animation(param1) {
    .db 0x5A, param1
}

; 0x7B: display_credit
.macro display_credit(param1, param2) {
    .db 0x7B, param1, param2
}

; 0xFF: exit
.macro exit() {
    .db 0xFF
}
