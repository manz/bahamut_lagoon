"""
Bahamut Lagoon room script macro library.

Generated from utils/vm/opcodes_map.py by generate_macros.py: edit the generator, not this file.
"""


.macro jump(address) {
    """Room opcode 0x00: jump."""
    .db 0x00
    .dw address
}

.macro conditional_jump_1(param1, param2) {
    """Room opcode 0x01: conditional_jump_1."""
    .db 0x01, param1, param2
}

.macro conditional_jump_2(param1, param2) {
    """Room opcode 0x02: conditional_jump_2."""
    .db 0x02, param1, param2
}

.macro conditional_subroutine(param1, param2) {
    """Room opcode 0x03: conditional_subroutine."""
    .db 0x03, param1, param2
}

.macro conditional_jump_4(param1, param2) {
    """Room opcode 0x04: conditional_jump_4."""
    .db 0x04, param1, param2
}

.macro jump_to_subroutine(address) {
    """Room opcode 0x05: jump_to_subroutine."""
    .db 0x05
    .dw address
}

.macro return_from_subroutine() {
    """Room opcode 0x06: return_from_subroutine."""
    .db 0x06
}

.macro yes_no(text_addr, yes_addr, no_addr) {
    """Room opcode 0x08: yes_no."""
    .db 0x08
    .dw text_addr
    .dw yes_addr
    .dw no_addr
}

.macro multiple_choice(text_addr, choice1, choice2, choice3, choice4) {
    """Room opcode 0x09: multiple_choice."""
    .db 0x09
    .dw text_addr
    .dw choice1
    .dw choice2
    .dw choice3
    .dw choice4
}

.macro set_state_bits() {
    """Room opcode 0x0C: set_state_bits."""
    .db 0x0C
}

.macro clear_state_bits() {
    """Room opcode 0x0D: clear_state_bits."""
    .db 0x0D
}

.macro actor_state(param1, param2) {
    """Room opcode 0x0E: actor_state."""
    .db 0x0E, param1, param2
}

.macro actor_speed(param1, param2) {
    """Room opcode 0x0F: actor_speed."""
    .db 0x0F, param1, param2
}

.macro actor_stuff_10(param1, param2) {
    """Room opcode 0x10: actor_stuff_10?."""
    .db 0x10, param1, param2
}

.macro actor_playable(param1) {
    """Room opcode 0x11: actor_playable."""
    .db 0x11, param1
}

.macro actor_show(param1, param2, param3) {
    """Room opcode 0x12: actor_show."""
    .db 0x12, param1, param2, param3
}

.macro actor_move() {
    """Room opcode 0x13: actor_move."""
    .db 0x13
}

.macro setup_scene_background(param1) {
    """Room opcode 0x1B: setup_scene_background."""
    .db 0x1B, param1
}

.macro setup_scene_mask(param1, param2) {
    """Room opcode 0x1C: setup_scene_mask."""
    .db 0x1C, param1, param2
}

.macro center_scene_on_background(param1, param2) {
    """Room opcode 0x27: center_scene_on_background?."""
    .db 0x27, param1, param2
}

.macro set_screen_status(param1) {
    """Room opcode 0x29: set_screen_status."""
    .db 0x29, param1
}

.macro animate_brightness(param1, param2, param3, param4) {
    """Room opcode 0x2A: animate_brightness."""
    .db 0x2A, param1, param2, param3, param4
}

.macro set_window_position(param1, param2) {
    """Room opcode 0x34: set_window_position."""
    .db 0x34, param1, param2
}

.macro set_window_style(param1) {
    """Room opcode 0x35: set_window_style."""
    .db 0x35, param1
}

.macro close_window() {
    """Room opcode 0x36: close_window."""
    .db 0x36
}

.macro display_text(text_address) {
    """Room opcode 0x37: display_text."""
    .db 0x37
    .dw text_address
}

.macro pause(param1) {
    """Room opcode 0x3F: pause."""
    .db 0x3F, param1
}

.macro player_control_flag(param1) {
    """Room opcode 0x42: player_control_flag."""
    .db 0x42, param1
}

.macro change_room(param1) {
    """Room opcode 0x43: change_room."""
    .db 0x43, param1
}

.macro init_state(param1, param2, param3, param4) {
    """Room opcode 0x44: init state."""
    .db 0x44, param1, param2, param3, param4
}

.macro wait_for_actor_to_be_still(param1) {
    """Room opcode 0x48: wait_for_actor_to_be_still."""
    .db 0x48, param1
}

.macro show_mode7_animation(param1) {
    """Room opcode 0x5A: show_mode7_animation."""
    .db 0x5A, param1
}

.macro display_credit(param1, param2) {
    """Room opcode 0x7B: display_credit."""
    .db 0x7B, param1, param2
}

.macro exit() {
    """Room opcode 0xFF: exit."""
    .db 0xFF
}
