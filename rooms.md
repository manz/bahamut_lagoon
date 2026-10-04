# Bahamut Lagoon Room Script Documentation

## Room Structure

Bahamut Lagoon uses a virtual machine architecture for room scripting. Each room contains bytecode instructions that control game events, dialog display, character movement, scene transitions, and player interactions.

### Room Header (12 bytes)

```
Offset  Purpose
------  -------
0x0000  Entry point (typically 0x08 or 0x0c)
0x0002  Actors table pointer
0x0004  Room 4 pointer (various events)
0x0006  Player events pointer
0x0008  Room 8 pointer (unused in most rooms)
0x000a  Room A pointer (unused in most rooms)
```

### Room Data Format

- **Compression**: Rooms may be compressed using LZSS-style algorithm
- **Memory limit**: 0x6000 byte decompression buffer
- **Text storage**: Text references use pointer tables, resolved at runtime
- **Execution model**: Stack-based VM with subroutine calls/returns

## Known Opcodes (34 documented)

### Control Flow
- `0x00`: `jump(address)` - Unconditional jump
- `0x01`: `conditional_jump_1(flag, address)` - Conditional jump type 1
- `0x02`: `conditional_jump_2(flag, address)` - Conditional jump type 2  
- `0x03`: `conditional_subroutine(flag, address)` - Conditional subroutine call
- `0x04`: `conditional_jump_4(flag, address)` - Conditional jump type 4
- `0x05`: `jump_to_subroutine(address)` - Call subroutine
- `0x06`: `return_from_subroutine()` - Return from subroutine
- `0xFF`: `exit()` - Exit room/end script

### State Management
- `0x0C`: `set_state_bits(flag_addr)` - Set game state bits
- `0x0D`: `clear_state_bits(flag_addr)` - Clear game state bits
- `0x42`: `player_control_flag(enable)` - Enable/disable player control
- `0x43`: `change_room(room_id)` - Change to different room
- `0x44`: `init_state(p1, p2, p3, p4)` - Initialize state memory

### Actor Control
- `0x0E`: `actor_state(actor_id, state)` - Set actor state
- `0x0F`: `actor_speed(actor_id, speed)` - Set actor movement speed
- `0x11`: `actor_playable(actor_id)` - Make actor player-controlled
- `0x12`: `actor_show(actor_id, x, y)` - Show actor at position
- `0x13`: `actor_move(actor_id, directions...)` - Move actor (variable length)
- `0x48`: `wait_for_actor_to_be_still(actor_id)` - Wait for actor to stop moving

### Scene Control
- `0x1B`: `setup_scene_background(bg_id)` - Set background
- `0x1C`: `setup_scene_mask(mask_id, param)` - Set scene mask
- `0x27`: `center_scene_on_background(actor_id, param)` - Center camera on actor
- `0x29`: `set_screen_status(on_off)` - Turn screen on/off
- `0x2A`: `animate_brightness(start, end, time, param)` - Fade in/out

### Dialog & UI
- `0x08`: `yes_no(text_addr, yes_addr, no_addr)` - Yes/No choice
- `0x09`: `multiple_choice(text_addr, c1, c2, c3, c4)` - Multiple choice menu
- `0x34`: `set_window_position(x, y)` - Position dialog window
- `0x35`: `set_window_style(style)` - Set window style (0=narration, 1=dialog)
- `0x36`: `close_window()` - Close dialog window
- `0x37`: `display_text(text_address)` - Display text string

### Timing & Animation
- `0x3F`: `pause(frames)` - Pause for specified frames
- `0x5A`: `show_mode7_animation(param)` - Show Mode7 animation
- `0x7B`: `display_credit(p1, p2)` - Display credits

## Unknown Opcodes Analysis

Based on analysis of 83 decompiled rooms, here are the most frequent unknown opcodes with hypotheses:

### High Confidence Identifications

**0x16** (1374 occurrences) - **Actor Facing Direction**
- Pattern: `actor_state(id, state) → 0x47(id) → 0x16(id, 1)`
- Parameters: `(actor_id, direction)` - second param almost always `0x1`
- Purpose: Sets which direction actor sprite faces

**0x47** (499 occurrences) - **Actor Enable/Visibility**  
- Pattern: Always appears right before `0x16` opcodes
- Parameters: `(actor_id)`
- Purpose: Makes actor visible/active before setting facing direction

### Medium Confidence Identifications  

**0x6d** (1050 occurrences) - **Sound/Music Control**
- Common values: `0xcc, 0x1d, 0xd0, 0xc2, 0x1c, 0xce`
- Context: Scene transitions and visual effects
- Purpose: Likely sound effect triggers or music control

**0x38** (560 occurrences) - **Action Trigger**
- Pattern: No parameters `()`
- Context: Before dialog and menu interactions  
- Purpose: Prepares for user input or triggers action state

**0x24** (959 occurrences) - **Visual/Sprite Effects**
- Parameters: 4 values, often in sequences
- Context: Used with other visual opcodes
- Purpose: Sprite manipulation or visual effects

### Lower Confidence Identifications

**0x2F** (515 occurrences) - **Palette/Color Effects**
- Parameters: 6 values, complex patterns
- Common pattern: `0xfe/0xfd/0xff, 0x0, time, 0x0, color_params...`
- Purpose: Palette manipulation or color effects

**0x17** (467 occurrences) - **Actor Flags/Properties**
- Parameters: `(actor_id, flag_type, value)`
- Context: Actor setup sequences
- Purpose: Set actor flags or properties

**0x4C** (258 occurrences) - **Actor Property Setting**
- Parameters: 3 values, first is often actor ID
- Context: Actor initialization
- Purpose: Set actor properties or attributes

**0x6C** (216 occurrences) - **Audio Control**  
- Parameters: 2 values
- Context: Scene changes
- Purpose: Audio/music control

**Other Unknowns**: `0x54, 0x6F, 0x56, 0x53, 0x45, 0x2E, 0x30, 0x6B, 0x7A` appear frequently but need more analysis.

## Development Tools

### Macro Library
Generated a816 assembler macros are available in `src/room_macros.s`:
```assembly
setup_scene_background(0x15)
actor_show(0x5, 0x8, 0x12)
display_text(text_label)
exit()
```

### Build System
Use `build_room.py` to compile assembly rooms:
```bash
python3 build_room.py
```

### Room Format Conversion
The decompiled room format can be converted to a816 assembly using pattern matching on the bytecode structure.

## Testing Strategy

To verify unknown opcode hypotheses:
1. **Create test rooms** with isolated opcode usage
2. **Patch into ROM** and observe in-game behavior  
3. **Compare contexts** where opcodes appear
4. **Cross-reference** with other SNES games using similar engines

## Next Steps

1. **Implement unknown opcodes** in macro library with hypothetical names
2. **Create test harness** for ROM patching and testing
3. **Document actor states** and movement patterns
4. **Analyze text encoding** and pointer management
5. **Build visual room editor** using identified opcode patterns