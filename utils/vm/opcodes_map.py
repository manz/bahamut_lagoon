from utils.vm.opcodes import *

opcode_names = {
    0x00: 'jump',
    0x01: 'conditional_jump_1',
    0x02: 'conditional_jump_2',
    0x03: 'conditional_subroutine',
    0x04: 'conditional_jump_4',
    0x05: 'jump_to_subroutine',
    0x06: 'return_from_subroutine',
    0x08: 'yes_no',
    0x09: 'multiple_choice',
    0x0C: 'set_state_bits',
    0x0D: 'clear_state_bits',
    0x0E: 'actor_state',
    0x0F: 'actor_speed',
    0x10: 'actor_stuff_10?',
    0x11: 'actor_playable',
    0x12: 'actor_show',
    0x13: 'actor_move',

    0x27: 'center_scene_on_background?',
    0x34: 'set_window_position',
    0x1b: 'setup_scene_background',
    0x1c: 'setup_scene_mask',

    0x29: 'set_screen_status',

    # 0 for opening titles #1 for windowed text
    0x35: 'set_window_style',
    0x36: 'close_window',
    0x37: 'display_text',

    # 0x48: 'select_actor?',  # meh ?
    0x42: 'player_control_flag',
    0x43: 'change_room',
    0x48: 'wait_for_actor_to_be_still',
    0x5a: 'show_mode7_animation',  # but 0x01 leads to semi functional title screen
    0xff: 'exit'
}

opcode_table = {
    0x00: Jump(),
    0x01: ConditionalJump(),
    0x02: ConditionalJump(),
    0x03: ConditionalJumpToSubRoutine(),
    0x04: ConditionalJump(),

    0x05: JumpToSubRoutine(),
    0x06: ReturnFromSubRoutine(),

    0x07: Opcode(4),  # contains a Jump reference but to be checked

    0x08: YesNoChoiceOpcode(),
    0x09: MultipleChoiceTextOpcode(),
    # 0x0b 06 0a
    0x0a: Opcode(3),
    0x0b: Opcode(1),
    0x0c: StateOpcode(),
    # 0x0c: Opcode(2),
    0x0d: StateOpcode(),
    # 0x0d: Opcode(2),
    0x0e: Opcode(3,
                 comment_lambda=lambda r: f'actor({r.get_byte(1):#02x}) state({r.get_byte(2):#02x})'),
    0x0f: Opcode(3,
                 comment_lambda=lambda r: f'actor({ r.get_byte(1):#02x}) speed({r.get_byte(2)})'),

    0x10: Opcode(3),
    0x11: Opcode(2, comment_lambda=lambda r: f'actor({r.get_byte(1):#02x})'),
    0x12: Opcode(4,
                 comment_lambda=lambda
                     r: f'actor({r.get_byte(1):#02x}): x({r.get_byte(2):#02x}), y({r.get_byte(3):#02x})'),
    0x13: Opcode13(),
    0x14: Opcode13(),
    0x15: Opcode(3),
    0x16: Opcode(3),
    0x17: Opcode(3),
    0x18: Opcode18(),
    0x19: Opcode(3),
    0x1a: Opcode(3),
    0x1b: Opcode(2),
    0x1c: Opcode(3),
    0x1d: Opcode(4),
    0x1e: Opcode(5),
    0x1f: Opcode(5),

    0x20: Opcode(5),
    0x21: Opcode(3),
    0x22: Opcode(2),
    0x23: Opcode(3),
    0x24: Opcode(5),
    0x25: Opcode(5),
    0x26: Opcode(4),
    0x27: Opcode(3, comment_lambda=lambda r: f'actor({r.get_byte(1):#02x})'),
    0x28: Opcode(2),
    0x29: Opcode(2,
                 comment_lambda=lambda r: 'screen({})'.format('ON' if r.get_byte(1) else 'OFF') + ' OFF if 0 else ON'),
    0x2a: Opcode(5),
    0x2b: Opcode(2),
    0x2c: Opcode(5),
    0x2d: Opcode(3),
    0x2e: Opcode(0xa),
    0x2F: Opcode(7),

    0x30: Opcode(0xb),
    0x31: Opcode(4),
    0x32: Opcode(5),
    0x33: Opcode(4),
    0x34: Opcode(3),
    0x35: Opcode(2),
    0x36: Opcode(1),
    0x37: TextOpcode(),  # display text opcode
    0x38: Opcode(1),
    0x39: Opcode(2),
    0x3A: Opcode(2),
    0x3b: Opcode(2),
    0x3c: Opcode(2),
    0x3d: Opcode(3),
    0x3e: Opcode(3),
    0x3f: Opcode(2),

    0x40: Opcode(3),
    0x41: Opcode(2),
    0x42: Opcode(2),
    0x43: Opcode(2),  # Change room
    0x44: Opcode(5),  # inits first 4 bytes from the "state memory"
    0x45: Opcode(3),
    0x46: Opcode(1),
    0x47: Opcode(2),
    0x48: Opcode(2, comment_lambda=lambda r: f'actor({r.get_byte(1):#02x})'),
    0x49: Opcode(3),
    0x4a: Opcode(3),
    0x4b: Opcode(3),
    0x4c: Opcode(4),
    0x4d: Opcode(3),
    0x4e: Opcode(2),
    0x4f: Opcode(2),

    0x50: IfElseOpcode(),  # 0x50 seems to directly increment the pointer 0x6A
    0x51: Opcode(5),
    0x52: Opcode(3),
    0x53: Opcode(3),
    0x54: Opcode(3),
    0x55: Opcode(6),
    0x56: Opcode(5),
    0x57: Opcode(5),
    0x58: Opcode(5),
    0x59: Opcode(7),
    0x5A: Opcode(2),
    0x5b: Opcode(0xd),
    0x5c: Opcode(2),
    0x5d: Opcode(7),
    0x5e: Opcode(7),
    0x5f: Opcode(2),

    0x60: Opcode(2),
    0x61: Opcode(2),
    0x62: Opcode(2),
    0x63: Opcode(2),
    0x64: Opcode(8),
    0x65: Opcode(7),
    0x66: Opcode(8),
    0x67: Opcode(2),
    0x68: Opcode(9),
    0x69: Opcode(2),
    0x6A: Opcode(9),
    0x6b: Opcode(3),
    0x6c: Opcode(3),
    0x6d: Opcode(2),
    0x6e: Opcode(3),
    0x6f: Opcode(3),

    0x70: Opcode(8),
    0x71: Opcode(2),
    0x72: Opcode(9),  # might be 8 for some reason was 2 JUMP
    0x73: Opcode(2),
    0x74: Opcode(2),
    0x75: Opcode(2),
    0x76: Opcode(1),
    0x77: Opcode(6),
    0x78: Opcode(6),
    0x79: Opcode(1),
    0x7a: Opcode(6),
    0x7b: TextOpcode(),
    # 0x7b: Opcode(3),  # Contains text display
    0x7c: Opcode(2),
    0x7d: Opcode(3),
    0x7e: Opcode(3),
    0x7F: Opcode(3),

    # 0x80: Opcode(2), # 3
    # 0x81: None, # 3
    # 0x82: Opcode(5), # 2
    # 0x83: Opcode(1), # 2
    # 0x84: Opcode(1), # 5
    # 0x85: Opcode(5), # 4
    # 0x86: Opcode(1),
    # 0x87: Opcode(1), # 5
    # 0x88: Opcode(2), # 1
    # 0x89: Opcode(2), # 1
    # 0x8a: Opcode(2), # 2
    # 0x8b: Opcode(2), # 2
    # 0x8c: None, # 2
    # 0x8d: None, # 2
    # 0x8e: None, # 3
    # 0x8f: Opcode(6),  # contains a jump (conditional)

    0x80: Opcode(2),
    0x81: Opcode(2),
    0x82: Opcode(5),
    0x83: Opcode(4),
    0x84: Opcode(1),
    0x85: Opcode(5),
    0x86: Opcode(1),
    0x87: Opcode(1),
    0x88: Opcode(2),
    0x89: Opcode(2),
    0x8a: Opcode(2),
    0x8b: Opcode(2),
    0x8c: Opcode(3),
    0x8d: Opcode(6),  # jump_00
    0x8e: Opcode(2),
    0x8f: Opcode(3),

    0x90: Opcode(7),
    0x91: Opcode(2),
    0x92: Opcode(3),
    0x93: Opcode(2),
    0x94: NinetySixOpcode(),
    # 0x95: Opcode(2),
    #  0x96: NinetySixOpcode(),
    # 0x96: Opcode(5),  # XX YY JUMP_16 contains a Jump address at the end of data,


    0x9E: Opcode(1, comment_lambda=lambda r: "Should not be executed because it traps the vm"),

    # opcodes > 94 does not have implementation and does not increment PC
    # should raise an exception because these opcodes do nothing and does not increment
    # the program counter hence throwing the game in infinite loop,
    # They are _NOT_ used in "production room code", indicates an error

    0xff: Opcode(1)
}

# Battle opcodes

nop_opcode = Opcode(2, comment_lambda=lambda r: "No operation")

battle_opcode_names = {
    0x26: 'display_text',
    0xff: 'exit'
}

battle_opcode_table = {
    0x0: Jump(),  # Opcode(3),  # Opcode(8), # dubious
    0x1: BattleOptionalJump(),  # Opcode(3),
    0x2: BattleOptionalJump(),  # Opcode(3),
    0x3: BattleOptionalJump(),
    0x5: BattleOptionalJump(),  # Opcode(3),
    0x4: nop_opcode,
    0x6: BattleOptionalJump(),  # Opcode(3),
    0x7: Opcode(2),
    0x8: Opcode(1),
    0xa: Opcode(3),
    0xb: Opcode(1),
    0xc: BattleOptionalJump(),
    0xd: BattleOptionalJump(),
    0xe: ConditionalJump(),
    0xf: ConditionalJump(),

    0x10: Opcode(2),
    0x11: Opcode(2),
    0x12: Opcode(1),
    0x13: Opcode(1),
    0x14: Opcode(2),
    0x15: Opcode(2),
    0x16: Opcode(2),
    0x17: Opcode(3),
    0x18: Opcode(1),
    0x19: Opcode(1),
    0x1b: Opcode(2),
    0x1c: Opcode(1),
    0x1d: Opcode(2),
    0x1f: Opcode(1),
    0x20: Opcode(1),
    0x22: Opcode(1),
    0x24: Opcode(1),
    0x25: Opcode(1),
    0x26: TextOpcode(),
    0x28: Opcode(2),
    0x29: Opcode(1),
    0x2a: Opcode(3),
    0x2C: Opcode(1),  # calls display_battle_string manual
    0x31: Opcode(4),
    0x33: Opcode(3),
    0x35: Opcode(2),
    0x36: Opcode(1),
    0x37: Opcode(1),
    0x38: Opcode(2),
    0x39: Opcode(1),
    0x3a: Opcode(2),
    0x3b: Opcode(2),
    0x40: Opcode(1),
    0x41: Opcode(1),
    0x42: Opcode(1),
    0x43: Opcode(3),
    0x44: Opcode(2),
    0x45: Opcode(1),
    0x4A: nop_opcode,
    0x50: Opcode(2),  # jumps to an address loaded from 7F0000 + an index
    0x52: ConditionalJump(),
    0x53: ConditionalJump(),
    0x60: Opcode(2),
    0x61: Opcode(2),
    0x62: Opcode(2),
    0x63: Opcode(2),
    0x64: Opcode(1),
    0x65: Opcode(1),
    0x66: Opcode(5),
    0x68: Opcode(3),
    0x6a: Opcode(5),
    0x6b: Opcode(3),
    0x6c: Opcode(1),
    0x6d: Opcode(1),
    0x6e: Opcode(1),
    0x74: nop_opcode,
    0x7C: nop_opcode,
    0x80: nop_opcode,
    0x90: Opcode(2),
    0x92: Opcode(1),
    0xb1: nop_opcode,
    0xc7: nop_opcode,
    0xde: nop_opcode,
    0xe1: nop_opcode,
    0xe5: nop_opcode,
    0xeb: nop_opcode,
    0xf0: Opcode(2),
    0xf1: Opcode(5),
    0xf3: Opcode(3),
    0xf4: Opcode(2),
    0xf5: Opcode(1),
    0xf6: Opcode(1),
    0xf7: Opcode(3),
    0xf8: Opcode(3),
    0xf9: Opcode(2),
    0xfe: nop_opcode,
    0xff: Opcode(1),
}
