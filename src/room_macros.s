"""
Bahamut Lagoon room script macro library.

Generated from utils/vm/opcodes_map.py by generate_macros.py: edit the generator, not this file.
"""


.macro jump(address) {
    """Room opcode 0x00: jump."""
    .db 0x00
    .dw address
}

.macro jump_if_room_bits(param1, address) {
    """Room opcode 0x01: jump_if_room_bits."""
    .db 0x01, param1
    .dw address
}

.macro jump_unless_room_bits(param1, address) {
    """Room opcode 0x02: jump_unless_room_bits."""
    .db 0x02, param1
    .dw address
}

.macro jump_if_flag(param1, address) {
    """Room opcode 0x03: jump_if_flag."""
    .db 0x03, param1
    .dw address
}

.macro jump_unless_flag(param1, address) {
    """Room opcode 0x04: jump_unless_flag."""
    .db 0x04, param1
    .dw address
}

.macro call(address) {
    """Room opcode 0x05: call."""
    .db 0x05
    .dw address
}

.macro return() {
    """Room opcode 0x06: return."""
    .db 0x06
}

.macro jump_if_item(param1, address) {
    """Room opcode 0x07: jump_if_item."""
    .db 0x07, param1
    .dw address
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

.macro loop_start(param1, param2) {
    """Room opcode 0x0A: loop_start."""
    .db 0x0A, param1, param2
}

.macro loop_end() {
    """Room opcode 0x0B: loop_end."""
    .db 0x0B
}

.macro set_flag() {
    """Room opcode 0x0C: set_flag."""
    .db 0x0C
}

.macro clear_flag() {
    """Room opcode 0x0D: clear_flag."""
    .db 0x0D
}

.macro actor_set_frame(param1, param2) {
    """Room opcode 0x0E: actor_set_frame."""
    .db 0x0E, param1, param2
}

.macro actor_set_speed(param1, param2) {
    """Room opcode 0x0F: actor_set_speed."""
    .db 0x0F, param1, param2
}

.macro actor_set_anim_rate(param1, param2) {
    """Room opcode 0x10: actor_set_anim_rate."""
    .db 0x10, param1, param2
}

.macro set_player_actor(param1) {
    """Room opcode 0x11: set_player_actor."""
    .db 0x11, param1
}

.macro actor_place(param1, param2, param3) {
    """Room opcode 0x12: actor_place."""
    .db 0x12, param1, param2, param3
}

.macro actor_move(actor, motion, end) {
    """Room opcode 0x13: actor_move."""
    .db 0x13, actor, motion, end
}

.macro actors_hold(actor, end) {
    """Room opcode 0x14: actors_hold."""
    .db 0x14, actor, end
}

.macro set_follower(param1, param2) {
    """Room opcode 0x15: set_follower."""
    .db 0x15, param1, param2
}

.macro actor_set_animated(param1, param2) {
    """Room opcode 0x16: actor_set_animated."""
    .db 0x16, param1, param2
}

.macro actor_set_behavior(param1, param2) {
    """Room opcode 0x17: actor_set_behavior."""
    .db 0x17, param1, param2
}

.macro actors_release(actor, end) {
    """Room opcode 0x18: actors_release."""
    .db 0x18, actor, end
}

.macro actor_set_palette(param1, param2) {
    """Room opcode 0x19: actor_set_palette."""
    .db 0x19, param1, param2
}

.macro store_actor_facing(param1, param2) {
    """Room opcode 0x1A: store_actor_facing."""
    .db 0x1A, param1, param2
}

.macro load_map(param1) {
    """Room opcode 0x1B: load_map."""
    .db 0x1B, param1
}

.macro set_camera(param1, param2) {
    """Room opcode 0x1C: set_camera."""
    .db 0x1C, param1, param2
}

.macro scroll_camera(param1, param2, param3) {
    """Room opcode 0x1D: scroll_camera."""
    .db 0x1D, param1, param2, param3
}

.macro layer_motion_1(param1, param2, param3, param4) {
    """Room opcode 0x1E: layer_motion_1."""
    .db 0x1E, param1, param2, param3, param4
}

.macro layer_motion_2(param1, param2, param3, param4) {
    """Room opcode 0x1F: layer_motion_2."""
    .db 0x1F, param1, param2, param3, param4
}

.macro layer_motion_3(param1, param2, param3, param4) {
    """Room opcode 0x20: layer_motion_3."""
    .db 0x20, param1, param2, param3, param4
}

.macro actor_set_layer(param1, param2) {
    """Room opcode 0x21: actor_set_layer."""
    .db 0x21, param1, param2
}

.macro set_state_3f_20(param1) {
    """Room opcode 0x22: set_state_3f_20."""
    .db 0x22, param1
}

.macro layer_bg1(param1, param2) {
    """Room opcode 0x23: layer_bg1."""
    .db 0x23, param1, param2
}

.macro map_set_tile_bg1(param1, param2, param3, param4) {
    """Room opcode 0x24: map_set_tile_bg1."""
    .db 0x24, param1, param2, param3, param4
}

.macro map_set_tile_bg2(param1, param2, param3, param4) {
    """Room opcode 0x25: map_set_tile_bg2."""
    .db 0x25, param1, param2, param3, param4
}

.macro map_set_attribute(param1, param2, param3) {
    """Room opcode 0x26: map_set_attribute."""
    .db 0x26, param1, param2, param3
}

.macro scroll_camera_to_actor(param1, param2) {
    """Room opcode 0x27: scroll_camera_to_actor."""
    .db 0x27, param1, param2
}

.macro set_state_3c_20(param1) {
    """Room opcode 0x28: set_state_3c_20."""
    .db 0x28, param1
}

.macro set_screen(param1) {
    """Room opcode 0x29: set_screen."""
    .db 0x29, param1
}

.macro fade_brightness(param1, param2, param3, param4) {
    """Room opcode 0x2A: fade_brightness."""
    .db 0x2A, param1, param2, param3, param4
}

.macro set_brightness(param1) {
    """Room opcode 0x2B: set_brightness."""
    .db 0x2B, param1
}

.macro fade_mosaic(param1, param2, param3, param4) {
    """Room opcode 0x2C: fade_mosaic."""
    .db 0x2C, param1, param2, param3, param4
}

.macro set_mosaic(param1, param2) {
    """Room opcode 0x2D: set_mosaic."""
    .db 0x2D, param1, param2
}

.macro color_effect(param1, param2, param3, param4, param5, param6, param7, param8, param9) {
    """Room opcode 0x2E: color_effect."""
    .db 0x2E, param1, param2, param3, param4, param5, param6, param7, param8, param9
}

.macro palette_fade_uniform(param1, param2, param3, param4, param5, param6) {
    """Room opcode 0x2F: palette_fade_uniform."""
    .db 0x2F, param1, param2, param3, param4, param5, param6
}

.macro palette_fade_rgb(param1, param2, param3, param4, param5, param6, param7, param8, param9, param10) {
    """Room opcode 0x30: palette_fade_rgb."""
    .db 0x30, param1, param2, param3, param4, param5, param6, param7, param8, param9, param10
}

.macro palette_restore(param1, param2, param3) {
    """Room opcode 0x31: palette_restore."""
    .db 0x31, param1, param2, param3
}

.macro palette_effect_32(param1, param2, param3, param4) {
    """Room opcode 0x32: palette_effect_32."""
    .db 0x32, param1, param2, param3, param4
}

.macro palette_effect_33(param1, param2, param3) {
    """Room opcode 0x33: palette_effect_33."""
    .db 0x33, param1, param2, param3
}

.macro set_window_position(param1, param2) {
    """Room opcode 0x34: set_window_position."""
    .db 0x34, param1, param2
}

.macro open_window(param1) {
    """Room opcode 0x35: open_window."""
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

.macro clear_window_text() {
    """Room opcode 0x38: clear_window_text."""
    .db 0x38
}

.macro give_item(param1) {
    """Room opcode 0x39: give_item."""
    .db 0x39, param1
}

.macro take_item(param1) {
    """Room opcode 0x3A: take_item."""
    .db 0x3A, param1
}

.macro restore_hp(param1) {
    """Room opcode 0x3B: restore_hp."""
    .db 0x3B, param1
}

.macro restore_mp(param1) {
    """Room opcode 0x3C: restore_mp."""
    .db 0x3C, param1
}

.macro add_money(param1, param2) {
    """Room opcode 0x3D: add_money."""
    .db 0x3D, param1, param2
}

.macro remove_money(param1, param2) {
    """Room opcode 0x3E: remove_money."""
    .db 0x3E, param1, param2
}

.macro wait_frames(param1) {
    """Room opcode 0x3F: wait_frames."""
    .db 0x3F, param1
}

.macro set_word_0329(param1, param2) {
    """Room opcode 0x40: set_word_0329."""
    .db 0x40, param1, param2
}

.macro set_state_3c_80(param1) {
    """Room opcode 0x41: set_state_3c_80."""
    .db 0x41, param1
}

.macro player_control(param1) {
    """Room opcode 0x42: player_control."""
    .db 0x42, param1
}

.macro change_room(param1) {
    """Room opcode 0x43: change_room."""
    .db 0x43, param1
}

.macro set_game_state(param1, param2, param3, param4) {
    """Room opcode 0x44: set_game_state."""
    .db 0x44, param1, param2, param3, param4
}

.macro set_state_0327(param1, param2) {
    """Room opcode 0x45: set_state_0327."""
    .db 0x45, param1, param2
}

.macro set_state_3d_10() {
    """Room opcode 0x46: set_state_3d_10."""
    .db 0x46
}

.macro wait_actor_animation(param1) {
    """Room opcode 0x47: wait_actor_animation."""
    .db 0x47, param1
}

.macro wait_actor_move(param1) {
    """Room opcode 0x48: wait_actor_move."""
    .db 0x48, param1
}

.macro palette_commit(param1, param2) {
    """Room opcode 0x49: palette_commit."""
    .db 0x49, param1, param2
}

.macro layer_bg2(param1, param2) {
    """Room opcode 0x4A: layer_bg2."""
    .db 0x4A, param1, param2
}

.macro layer_bg3(param1, param2) {
    """Room opcode 0x4B: layer_bg3."""
    .db 0x4B, param1, param2
}

.macro actor_set_b811(param1, param2, param3) {
    """Room opcode 0x4C: actor_set_b811."""
    .db 0x4C, param1, param2, param3
}

.macro actor_set_facing(param1, param2) {
    """Room opcode 0x4D: actor_set_facing."""
    .db 0x4D, param1, param2
}

.macro set_tile_priority_a(param1) {
    """Room opcode 0x4E: set_tile_priority_a."""
    .db 0x4E, param1
}

.macro set_tile_priority_b(param1) {
    """Room opcode 0x4F: set_tile_priority_b."""
    .db 0x4F, param1
}

.macro random_branch() {
    """Room opcode 0x50: random_branch."""
    .db 0x50
}

.macro load_palette(param1, param2, param3, param4) {
    """Room opcode 0x51: load_palette."""
    .db 0x51, param1, param2, param3, param4
}

.macro layer_obj(param1, param2) {
    """Room opcode 0x52: layer_obj."""
    .db 0x52, param1, param2
}

.macro save_actor_position(param1, param2) {
    """Room opcode 0x53: save_actor_position."""
    .db 0x53, param1, param2
}

.macro restore_actor_position(param1, param2) {
    """Room opcode 0x54: restore_actor_position."""
    .db 0x54, param1, param2
}

.macro actor_set_b813(param1, param2, param3, param4, param5) {
    """Room opcode 0x55: actor_set_b813."""
    .db 0x55, param1, param2, param3, param4, param5
}

.macro set_var(param1, param2, param3, param4) {
    """Room opcode 0x56: set_var."""
    .db 0x56, param1, param2, param3, param4
}

.macro or_var(param1, param2, param3, param4) {
    """Room opcode 0x57: or_var."""
    .db 0x57, param1, param2, param3, param4
}

.macro and_var(param1, param2, param3, param4) {
    """Room opcode 0x58: and_var."""
    .db 0x58, param1, param2, param3, param4
}

.macro copy_byte(param1, param2, param3, param4, param5, param6) {
    """Room opcode 0x59: copy_byte."""
    .db 0x59, param1, param2, param3, param4, param5, param6
}

.macro show_mode7_animation(param1) {
    """Room opcode 0x5A: show_mode7_animation."""
    .db 0x5A, param1
}

.macro setup_windows(
    param1,
    param2,
    param3,
    param4,
    param5,
    param6,
    param7,
    param8,
    param9,
    param10,
    param11,
    param12,
) {
    """Room opcode 0x5B: setup_windows."""
    .db 0x5B, param1, param2, param3, param4, param5, param6, param7, param8, param9, param10, param11, param12
}

.macro load_graphics_5c(param1) {
    """Room opcode 0x5C: load_graphics_5c."""
    .db 0x5C, param1
}

.macro animate_window_1(param1, param2, param3, param4, param5, param6) {
    """Room opcode 0x5D: animate_window_1."""
    .db 0x5D, param1, param2, param3, param4, param5, param6
}

.macro animate_window_2(param1, param2, param3, param4, param5, param6) {
    """Room opcode 0x5E: animate_window_2."""
    .db 0x5E, param1, param2, param3, param4, param5, param6
}

.macro start_effect_5f(param1) {
    """Room opcode 0x5F: start_effect_5f."""
    .db 0x5F, param1
}

.macro set_state_40_20(param1) {
    """Room opcode 0x60: set_state_40_20."""
    .db 0x60, param1
}

.macro set_state_40_40(param1) {
    """Room opcode 0x61: set_state_40_40."""
    .db 0x61, param1
}

.macro set_room_bits(param1) {
    """Room opcode 0x62: set_room_bits."""
    .db 0x62, param1
}

.macro clear_room_bits(param1) {
    """Room opcode 0x63: clear_room_bits."""
    .db 0x63, param1
}

.macro dma_to_vram(param1, param2, param3, param4, param5, param6, param7) {
    """Room opcode 0x64: dma_to_vram."""
    .db 0x64, param1, param2, param3, param4, param5, param6, param7
}

.macro lz_decompress(param1, param2, param3, param4, param5, param6) {
    """Room opcode 0x65: lz_decompress."""
    .db 0x65, param1, param2, param3, param4, param5, param6
}

.macro object_create(param1, param2, param3, param4, param5, param6, param7) {
    """Room opcode 0x66: object_create."""
    .db 0x66, param1, param2, param3, param4, param5, param6, param7
}

.macro object_remove(param1) {
    """Room opcode 0x67: object_remove."""
    .db 0x67, param1
}

.macro copy_block(param1, param2, param3, param4, param5, param6, param7, param8) {
    """Room opcode 0x68: copy_block."""
    .db 0x68, param1, param2, param3, param4, param5, param6, param7, param8
}

.macro set_bits_3b(param1) {
    """Room opcode 0x69: set_bits_3b."""
    .db 0x69, param1
}

.macro sound_reset() {
    """Room opcode 0x6A: sound_reset."""
    .db 0x6A
}

.macro play_music(param1, param2) {
    """Room opcode 0x6B: play_music."""
    .db 0x6B, param1, param2
}

.macro sound_command_13(param1, param2) {
    """Room opcode 0x6C: sound_command_13."""
    .db 0x6C, param1, param2
}

.macro play_sound(param1) {
    """Room opcode 0x6D: play_sound."""
    .db 0x6D, param1
}

.macro sound_command_13_b(param1, param2) {
    """Room opcode 0x6E: sound_command_13_b."""
    .db 0x6E, param1, param2
}

.macro sound_command_12(param1, param2) {
    """Room opcode 0x6F: sound_command_12."""
    .db 0x6F, param1, param2
}

.macro jump_if_actor_in_area(param1, param2, param3, param4, param5, address) {
    """Room opcode 0x70: jump_if_actor_in_area."""
    .db 0x70, param1, param2, param3, param4, param5
    .dw address
}

.macro set_state_40_80(param1) {
    """Room opcode 0x71: set_state_40_80."""
    .db 0x71, param1
}

.macro start_effect_task(param1, param2, param3, param4, param5, param6, param7, param8) {
    """Room opcode 0x72: start_effect_task."""
    .db 0x72, param1, param2, param3, param4, param5, param6, param7, param8
}

.macro set_state_42(param1) {
    """Room opcode 0x73: set_state_42."""
    .db 0x73, param1
}

.macro window_1(param1) {
    """Room opcode 0x74: window_1."""
    .db 0x74, param1
}

.macro window_2(param1) {
    """Room opcode 0x75: window_2."""
    .db 0x75, param1
}

.macro windows_off() {
    """Room opcode 0x76: windows_off."""
    .db 0x76
}

.macro effect_77(param1, param2, param3, param4, param5) {
    """Room opcode 0x77: effect_77."""
    .db 0x77, param1, param2, param3, param4, param5
}

.macro effect_78(param1, param2, param3, param4, param5) {
    """Room opcode 0x78: effect_78."""
    .db 0x78, param1, param2, param3, param4, param5
}

.macro stop_effect_task() {
    """Room opcode 0x79: stop_effect_task."""
    .db 0x79
}

.macro start_effect_7a(param1, param2, param3, param4, param5) {
    """Room opcode 0x7A: start_effect_7a."""
    .db 0x7A, param1, param2, param3, param4, param5
}

.macro display_credit(param1, param2) {
    """Room opcode 0x7B: display_credit."""
    .db 0x7B, param1, param2
}

.macro set_state_41_08(param1) {
    """Room opcode 0x7C: set_state_41_08."""
    .db 0x7C, param1
}

.macro layer_velocity_a(param1, param2) {
    """Room opcode 0x7D: layer_velocity_a."""
    .db 0x7D, param1, param2
}

.macro layer_velocity_b(param1, param2) {
    """Room opcode 0x7E: layer_velocity_b."""
    .db 0x7E, param1, param2
}

.macro set_layer_position(param1, param2) {
    """Room opcode 0x7F: set_layer_position."""
    .db 0x7F, param1, param2
}

.macro setup_unit_80(param1) {
    """Room opcode 0x80: setup_unit_80."""
    .db 0x80, param1
}

.macro select_units_81(param1) {
    """Room opcode 0x81: select_units_81."""
    .db 0x81, param1
}

.macro add_var(param1, param2, param3, param4) {
    """Room opcode 0x82: add_var."""
    .db 0x82, param1, param2, param3, param4
}

.macro actor_place_83(param1, param2, param3) {
    """Room opcode 0x83: actor_place_83."""
    .db 0x83, param1, param2, param3
}

.macro call_da748f() {
    """Room opcode 0x84: call_da748f."""
    .db 0x84
}

.macro draw_credit_line(param1, param2, param3, param4) {
    """Room opcode 0x85: draw_credit_line."""
    .db 0x85, param1, param2, param3, param4
}

.macro refresh_3b_40() {
    """Room opcode 0x86: refresh_3b_40."""
    .db 0x86
}

.macro call_da755c() {
    """Room opcode 0x87: call_da755c."""
    .db 0x87
}

.macro call_da781c(param1) {
    """Room opcode 0x88: call_da781c."""
    .db 0x88, param1
}

.macro set_state_41_20(param1) {
    """Room opcode 0x89: set_state_41_20."""
    .db 0x89, param1
}

.macro wait_object(param1) {
    """Room opcode 0x8A: wait_object."""
    .db 0x8A, param1
}

.macro toggle_8b(param1) {
    """Room opcode 0x8B: toggle_8b."""
    .db 0x8B, param1
}

.macro wait_frames_long(param1, param2) {
    """Room opcode 0x8C: wait_frames_long."""
    .db 0x8C, param1, param2
}

.macro jump_if_pad(param1, param2, param3, address) {
    """Room opcode 0x8D: jump_if_pad."""
    .db 0x8D, param1, param2, param3
    .dw address
}

.macro set_state_41_40(param1) {
    """Room opcode 0x8E: set_state_41_40."""
    .db 0x8E, param1
}

.macro actor_set_sprite_frame(param1, param2) {
    """Room opcode 0x8F: actor_set_sprite_frame."""
    .db 0x8F, param1, param2
}

.macro add_var_clamped(param1, param2, param3, param4, param5, param6) {
    """Room opcode 0x90: add_var_clamped."""
    .db 0x90, param1, param2, param3, param4, param5, param6
}

.macro call_ef0080(param1) {
    """Room opcode 0x91: call_ef0080."""
    .db 0x91, param1
}

.macro sound_command_11(param1, param2) {
    """Room opcode 0x92: sound_command_11."""
    .db 0x92, param1, param2
}

.macro set_map_priority(param1) {
    """Room opcode 0x93: set_map_priority."""
    .db 0x93, param1
}

.macro jump_if_actors_near(param1, param2, address) {
    """Room opcode 0x94: jump_if_actors_near."""
    .db 0x94, param1, param2
    .dw address
}

.macro exit() {
    """Room opcode 0xFF: exit."""
    .db 0xFF
}
