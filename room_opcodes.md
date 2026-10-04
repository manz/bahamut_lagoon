# Bahamut Lagoon Room Opcodes Reference

Complete reference for all room script opcodes, based on VM implementation analysis and decompiled room patterns.

## Known Opcodes (From VM Implementation)

### Control Flow Opcodes

#### 0x00 - jump(address)
**Unconditional jump to address**
- Size: 3 bytes (opcode + 16-bit address)
- Implementation: `Jump` class
- Effect: Sets PC to target address immediately
- Usage: `jump(label_name)`
- Example: `0x00 0x50 0x01` → jump to 0x0150

#### 0x01-0x02-0x04 - conditional_jump_N(flag, address)  
**Conditional jumps (types 1, 2, 4)**
- Size: 4 bytes (opcode + flag + 16-bit address)
- Implementation: `ConditionalJump` class
- Effect: Jumps to address if flag condition is met, continues otherwise
- VM behavior: Explores both paths during disassembly
- Usage: `conditional_jump_1(0x84, target_label)`
- Example: `0x01 0x84 0x50 0x01` → jump to 0x0150 if flag 0x84 set

#### 0x03 - conditional_subroutine(flag, address)
**Conditional subroutine call**
- Size: 4 bytes (opcode + flag + 16-bit address)
- Implementation: `ConditionalJumpToSubRoutine` class
- Effect: Calls subroutine if flag condition is met
- Stack: Pushes return address (PC + 4) onto stack
- Usage: `conditional_subroutine(0x88, subroutine_label)`
- Example: `0x03 0x88 0x85 0x05` → call 0x0585 if flag 0x88 set

#### 0x05 - jump_to_subroutine(address)
**Unconditional subroutine call**
- Size: 3 bytes (opcode + 16-bit address)
- Implementation: `JumpToSubRoutine` class
- Stack: Pushes return address (PC + 3) onto stack
- Usage: `jump_to_subroutine(subroutine_label)`
- Example: `0x05 0xEF 0x07` → call subroutine at 0x07EF

#### 0x06 - return_from_subroutine()
**Return from subroutine**
- Size: 1 byte
- Implementation: `ReturnFromSubRoutine` class
- Stack: Pops return address from stack and jumps to it
- Usage: `return_from_subroutine()`
- Example: `0x06`

#### 0x50 - if_else(address1, address2)
**If-else branch (battle rooms)**
- Size: 5 bytes (opcode + two 16-bit addresses)
- Implementation: `IfElseOpcode` class
- Effect: Conditional execution of two code paths
- VM behavior: Explores both paths during disassembly
- Usage: `.db 0x50` followed by addresses
- Example: `0x50 0x00 0x02 0x50 0x02` → if-else branch

#### 0xFF - exit()
**Exit room script**
- Size: 1 byte
- Implementation: Basic `Opcode(1)`
- Effect: Terminates room script execution
- Usage: `exit()`
- Example: `0xFF`

### State Management Opcodes

#### 0x0C - set_state_bits(flag_addr)
**Set game state bits**
- Size: 2 bytes
- Implementation: `StateOpcode` class with bit decoding
- Effect: Sets bits in game state memory using convert table
- Bit calculation: `index = flag_addr >> 3`, `bit = convert_table[flag_addr & 7]`
- Usage: `set_state_bits(0x80)`
- Example: `0x0C 0x80` → set bit at calculated position

#### 0x0D - clear_state_bits(flag_addr)  
**Clear game state bits**
- Size: 2 bytes
- Implementation: `StateOpcode` class (same as 0x0C)
- Effect: Clears bits in game state memory
- Usage: `clear_state_bits(0x85)`
- Example: `0x0D 0x85` → clear bit at calculated position

#### 0x42 - player_control_flag(enable)
**Enable/disable player control**
- Size: 2 bytes
- Implementation: `Opcode(2)`
- Usage: `player_control_flag(0x01)`
- Example: `0x42 0x00` → disable player control

#### 0x43 - change_room(room_id)
**Change to different room**
- Size: 2 bytes
- Implementation: `Opcode(2)`
- Usage: `change_room(0x46)`
- Example: `0x43 0xDC` → change to room 0xDC

#### 0x44 - init_state(p1, p2, p3, p4)
**Initialize state memory**
- Size: 5 bytes
- Implementation: `Opcode(5)` - initializes first 4 bytes of state memory
- Usage: `init_state(0x5, 0x0, 0x1, 0x2)`
- Example: `0x44 0x05 0x00 0x01 0x02`

### Actor Control Opcodes

#### 0x0E - actor_state(actor_id, state)
**Set actor state**
- Size: 3 bytes
- Implementation: `Opcode(3)` with comment lambda showing actor ID and state
- Comment format: `"actor(0x05) state(0x0D)"`
- Usage: `actor_state(0x5, 0x0D)`
- Example: `0x0E 0x05 0x0D` → set actor 5 to state 13

#### 0x0F - actor_speed(actor_id, speed)
**Set actor movement speed**
- Size: 3 bytes  
- Implementation: `Opcode(3)` with comment showing actor ID and speed value
- Comment format: `"actor(0x03) speed(8)"`
- Usage: `actor_speed(0x3, 0x08)`
- Example: `0x0F 0x03 0x08` → set actor 3 speed to 8

#### 0x10 - actor_stuff_10(param1, param2)
**Unknown actor operation**
- Size: 3 bytes
- Implementation: `Opcode(3)` - function unknown
- Usage: `.db 0x10, param1, param2`

#### 0x11 - actor_playable(actor_id)
**Make actor player-controlled**
- Size: 2 bytes
- Implementation: `Opcode(2)` with comment showing actor ID
- Comment format: `"actor(0x05)"`
- Usage: `actor_playable(0x5)`
- Example: `0x11 0x05` → player controls actor 5

#### 0x12 - actor_show(actor_id, x, y)
**Show actor at position**
- Size: 4 bytes
- Implementation: `Opcode(4)` with detailed position comment
- Comment format: `"actor(0x05): x(0x08), y(0x12)"`
- Usage: `actor_show(0x5, 0x08, 0x12)`
- Example: `0x12 0x05 0x08 0x12` → show actor 5 at (8, 18)

#### 0x13 - actor_move(actor_id, directions...)
**Move actor with direction sequence**
- Size: Variable (ends with 0xFE or 0xFF)
- Implementation: `Opcode13` class with motion decoding
- Direction encoding (from `decode_actor_motion`):
  - `0x00-0x0F`: up(steps) - `motion & 0xF0 == 0x00`
  - `0x10-0x1F`: down(steps) - `motion & 0xF0 == 0x10`
  - `0x20-0x2F`: left(steps) - `motion & 0xF0 == 0x20`
  - `0x30-0x3F`: right(steps) - `motion & 0xF0 == 0x30`
  - `0x40-0x4F`: up-left diagonal
  - `0x50-0x5F`: down-right diagonal
  - `0x60-0x6F`: down-left diagonal
  - `0x70-0x7F`: up-right diagonal
  - `0xF0-0xFC`: pause/wait
  - `0xFE/0xFF`: End sequence
- Steps: `quantity = motion & 0x0F`
- Comment: Decoded motion sequence like `"actor(0x05): right(0x03), down(0x02)"`
- Example: `0x13 0x05 0x33 0x12 0xFF` → actor 5 move right 3, down 2

#### 0x14 - actor_move variant
**Alternative actor movement**
- Size: Variable (same as 0x13)
- Implementation: `Opcode13` class (identical to 0x13)

#### 0x18 - multi_actor_operation(actors...)
**Operation on multiple actors**
- Size: Variable (ends with 0xFF)
- Implementation: `Opcode18` class
- Format: First byte is parameter, followed by actor list, ends with 0xFF
- Example: `0x18 0x09 0x0A 0x0B 0xFF` → operation on actors 9, 10, 11

#### 0x48 - wait_for_actor_to_be_still(actor_id)
**Wait for actor to stop moving**
- Size: 2 bytes
- Implementation: `Opcode(2)` with comment showing actor ID
- Comment format: `"actor(0x05)"`
- Usage: `wait_for_actor_to_be_still(0x5)`
- Example: `0x48 0x05` → wait for actor 5 to stop

### Scene Control Opcodes

#### 0x1B - setup_scene_background(bg_id)
**Set scene background**
- Size: 2 bytes
- Implementation: `Opcode(2)`
- Usage: `setup_scene_background(0x15)`
- Example: `0x1B 0x15` → load background 21

#### 0x1C - setup_scene_mask(mask_id, param)
**Set scene mask/layer**
- Size: 3 bytes
- Implementation: `Opcode(3)`
- Usage: `setup_scene_mask(0x00, 0x00)`
- Example: `0x1C 0x00 0x00` → set scene mask

#### 0x27 - center_scene_on_background(actor_id, param)
**Center camera on actor**
- Size: 3 bytes
- Implementation: `Opcode(3)` with comment showing actor ID
- Comment format: `"actor(0x05)"`
- Usage: `center_scene_on_background(0x5, 0x20)`
- Example: `0x27 0x05 0x20` → center camera on actor 5

#### 0x29 - set_screen_status(on_off)
**Turn screen on/off**
- Size: 2 bytes
- Implementation: `Opcode(2)` with detailed comment
- Comment format: `"screen(ON/OFF) OFF 0 ON anything"`
- Usage: `set_screen_status(0x01)`
- Example: `0x29 0x01` → turn screen on

#### 0x2A - animate_brightness(start, end, time, param)
**Animate screen brightness (fade)**
- Size: 5 bytes
- Implementation: `Opcode(5)` with detailed brightness comment
- Comment format: `"animate_brightness(start=0x0F, end=0x00, time=0x20, unknown=0x00)"`
- Usage: `animate_brightness(0x00, 0x0F, 0x20, 0x00)`
- Example: `0x2A 0x0F 0x00 0x20 0x00` → fade to black over 32 frames

### Dialog & UI Opcodes

#### 0x08 - yes_no(text_addr, yes_addr, no_addr)
**Yes/No choice dialog**
- Size: 7 bytes (opcode + 3 × 16-bit addresses)
- Implementation: `YesNoChoiceOpcode` class
- VM behavior: Extracts text from text_addr, explores both yes/no paths
- Text extraction: Uses `get_string_from_room` to decode text
- Usage: `yes_no(question_text, yes_handler, no_handler)`
- Example: `0x08 0xBE 0x13 0x0A 0x0A 0x01 0x0A` → show choice dialog

#### 0x09 - multiple_choice(text_addr, choice1, choice2, choice3, choice4)
**Multiple choice menu**
- Size: 9 bytes (opcode + text_addr + 4 choice addresses)
- Implementation: `MultipleChoiceTextOpcode` class
- VM behavior: Extracts intro text, explores all 4 choice paths
- Usage: `multiple_choice(menu_text, opt1, opt2, opt3, opt4)`
- Unused choices: Set to 0x0000
- Example: `0x09 0x6F 0x11 0xC6 0x09 0xAB 0x09 0xCC 0x09`

#### 0x34 - set_window_position(x, y)
**Position dialog window**
- Size: 3 bytes
- Implementation: `Opcode(3)`
- Usage: `set_window_position(0x0A, 0x06)`
- Example: `0x34 0x0A 0x06` → position window at (10, 6)

#### 0x35 - set_window_style(style)
**Set dialog window style**
- Size: 2 bytes
- Implementation: `Opcode(2)`
- Usage: `set_window_style(0x01)`
- Example: `0x35 0x01` → character dialog style

#### 0x36 - close_window()
**Close dialog window**
- Size: 1 byte
- Implementation: `Opcode(1)`
- Usage: `close_window()`
- Example: `0x36`

#### 0x37 - display_text(text_address)
**Display text string**
- Size: 3 bytes (opcode + 16-bit text address)
- Implementation: `TextOpcode` class
- Text processing: 
  - Uses `get_string_from_room` to extract and decode text
  - Handles Japanese text with `bl_prefix_lookup_chars` if needed
  - Terminates on 0xFF, 0xFD, or 0xFF 0xFF sequences
  - Stores text reference for pointer management
- Usage: `display_text(text_label)`
- Example: `0x37 0x0B 0x0C` → display text at 0x0C0B

#### 0x7B - display_credit(text_address)
**Display credits text**
- Size: 3 bytes (same structure as 0x37)
- Implementation: `TextOpcode` class (same as 0x37)
- Usage: For credit sequences
- Example: `0x7B 0x10 0x15` → display credit text

### Timing & Animation Opcodes

#### 0x3F - pause(frames)
**Pause execution**
- Size: 2 bytes
- Implementation: `Opcode(2)` with comment showing frame count
- Comment format: `"pause(0x20)"`
- Usage: `pause(0x20)`
- Example: `0x3F 0x40` → pause for 64 frames

#### 0x5A - show_mode7_animation(param)
**Show Mode7 animation**
- Size: 2 bytes
- Implementation: `Opcode(2)`
- Usage: `show_mode7_animation(0x03)`
- Example: `0x5A 0x03` → play Mode7 animation 3

### Large Parameter Opcodes

Multiple opcodes with large parameter counts (implementation details from opcodes_map.py):

- `0x2E`: 10 bytes (opcode + 9 parameters) - Complex visual effect
- `0x30`: 11 bytes (opcode + 10 parameters) - Advanced Mode7 effects  
- `0x2F`: 7 bytes (opcode + 6 parameters) - Palette effects
- `0x72`: 9 bytes (opcode + 8 parameters) - Battle system
- `0x70`: 8 bytes - Advanced graphics
- `0x68`: 9 bytes - System operation
- `0x6A`: 5 bytes - Audio control
- `0x5B`: 13 bytes - Large system operation

## Unknown Opcodes (Statistical Analysis)

### High Confidence Actor Opcodes

Based on VM pattern analysis and usage frequency from 83 decompiled rooms:

#### 0x16 - Actor Facing Direction (1374 occurrences)
**Set actor sprite facing direction**
- Size: 3 bytes
- Pattern: `actor_state(id, state) → 0x47(id) → 0x16(id, direction)`  
- Parameters: actor_id, direction (0x00=up, 0x01=right, 0x02=down, 0x03=left)
- Usage: `.db 0x16, actor_id, direction`

#### 0x47 - Actor Enable/Visibility (499 occurrences)
**Make actor visible/active**  
- Size: 2 bytes
- Pattern: Always precedes 0x16
- Parameters: actor_id
- Usage: `.db 0x47, actor_id`

#### 0x17 - Actor Properties (467 occurrences)
**Set actor flags or properties**
- Size: 3 bytes
- Parameters: actor_id, property_type, value
- Usage: `.db 0x17, actor_id, property_type`

### Audio/Music Opcodes

#### 0x6D - Sound Effects (1050 occurrences)
**Play sound effect**
- Size: 2 bytes  
- Common IDs: 0xCC, 0x1D, 0xD0, 0xC2, 0x1C, 0xCE
- Usage: `.db 0x6D, sound_id`

#### 0x6B - Music Control (144 occurrences)
**Background music control**
- Size: 3 bytes
- Usage: `.db 0x6B, music_command, parameter`

#### 0x6C - Audio Control (216 occurrences)
**Audio system control**
- Size: 3 bytes
- Usage: `.db 0x6C, control_type, parameter`

### System/UI Opcodes

#### 0x38 - Action Trigger (560 occurrences)
**Prepare for user input**
- Size: 1 byte
- Context: Before dialogs and menus
- Usage: `.db 0x38`

#### 0x24 - Visual Effects (959 occurrences)  
**Sprite/visual effects**
- Size: 5 bytes
- Usage: `.db 0x24, param1, param2, param3, param4`

## Text Encoding Details

From VM implementation (`get_string_from_room`):

### Text Termination
- `0xFF`: Standard text end
- `0xFD`: Alternative text end  
- `0xFF 0xFF`: Double-byte end sequence
- `0xFD 0xFF`: Mixed end sequence

### Japanese Text Handling
For Japanese text (`room.lang == "jp"`):
- Uses `bl_prefix_lookup_chars` function
- Handles prefix bytes 0xF0, 0xF1, 0xF2, 0xF3
- Maintains current prefix state across characters
- Prefix applied to all following characters until new prefix

### Text Processing Pipeline
1. Find text boundaries using termination sequences
2. Extract raw bytes from room data  
3. Apply Japanese prefix processing if needed
4. Decode using character table (`table.to_text`)
5. Store in program with pointer references for patching

## VM Execution Model

### Stack Management
- Subroutine calls push return address onto stack
- Return opcodes pop address and jump back
- Stack underflow triggers `AlreadyVisitedError`

### Control Flow Analysis  
- VM explores all possible execution paths during disassembly
- Uses `save_pc()`/`restore_pc()` to handle branching
- `AlreadyVisitedError` prevents infinite loops in analysis
- Labels automatically generated for jump targets

### Address Space
- Rooms have size limits (0x6000 decompression buffer)
- Outside jumps detected and handled
- Pointer references tracked for text patching

This comprehensive analysis provides the foundation for creating accurate room editors and understanding Bahamut Lagoon's sophisticated scripting system.