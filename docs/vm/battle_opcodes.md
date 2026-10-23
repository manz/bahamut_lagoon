# Battle opcodes

Every handler of the battle script VM (`battle_opcode_runner` C0:6F00, table C0:7C07), by opcode, as
`utils.vm.battle_script.OPS` names them. The kintsuki projects label each handler `bop_<name>`. Operands in order:
b byte, w word, j code address, t text address, i text-table index.

Confidence: **H** code read fully, **M** mechanism clear, meaning partly, **L** guess. **✓** executed in game by
`tests/test_battle_script.py` at the decoded address and size (that test checks decoding, not what the opcode does).
The turn meaning of `load_turn` was also checked in game.

## Format

- **Where**: one battle room per scenario, 24-bit pointers at C7:140F (32 rooms). Each is an LZ stream
  (`utils.dump_battle_rooms.decompress_block`) unpacked to $7F:C080. Its first word is the offset of the script.
  The bytes before it are map data: map events at $7F:C282 (`map_event`), tile data at $7F:C482+.
- **Base**: C0:7522 sets `$32` = $C080 + that word. Every j / t operand and every header word is relative to it.
- **Header** at the base:
  - 0x00-0x1B: 14 entry words. C0:6ED8 runs entry A. Stubs C0:6E52-6ED3 call them on battle events (below).
  - 0x1C: the area-trigger table: `x, y, w, h, flag` records up to a negative x (C0:68E0). The cursor ($90 / $91)
    inside a rectangle sets local flag `flag` (bit 7 set: clears flag & 7F).
  - 0x1E: the text table, words indexed by 23 / 28. No vanilla script uses it: in rooms that do not use it the
    word points at a few stray bytes.
- **Layout**: the code follows the header, then the area table, the text table and the texts.
- **State**: `$1A00` PC (bank $7F), `$1A02` reg (word; most results land there, FF = none), `$1A04` the P register
  saved by compare / arithmetic / tests (Z bit 1, N bit 7, C bit 0, read by the conditional ops), `$1A08` + `$1A20`
  loop stack, `$1A09` + `$1A40` call stack (8 entries each), `$1AC0` 256 local flags (cleared by C0:68D0).
- **Variables**: 0x60 bytes at $7E:3F90 (`load_var` / `store_var`, operand bit 7 = word). Vars 40-5F are the 256
  battle flags (`set_flag`, `jump_if_flag`). Vars 28-2E are the scripted action (6E), 39-3F the spawn parameters
  (3B). Room flags: 128 bytes at $7F:C000 (`set_room_flag`, `jump_if_room_flag`, `map_event`).
- **Units**: a unit operand of FF means the unit in reg. Units 00-0B are the player's (records $7E:2B50), 0C-1B the
  enemy's ($7E:3750). Their map record is at $1400 + C0:088C(unit). The current unit is `$B1` (record `$B2`).
- **Ending**: FF (`exit`) frees the unit markers and returns from the runner. `load_unit_byte` (91) also returns
  from the runner when its unit is invalid.

Entries, from callers (C0:0123 main loop) and a traced battle (scenario 00): 00, 01, 02 turn start in that order
(C0:9EC6; 02 also clears var 28); 03 after the player phase (C0:9F05); 04 end of the turn (C0:9F15); 07 a player
unit ended its move (C0:9660); 0A an enemy unit ended its move (C0:1A57); 0C before an action (both sides), 08 after
a player action, 0B after an enemy action (C0:0AFF, C0:2848, C0:1B1E; these set `$1A0E` = unit, `$1A0C` = `$3D`,
`$1A12`): M. 05 and 0D run from C0:9F3C after C0:E617 (battle over?), 09 from C0:D208: L. Entry 06 has no caller
found.

`utils/battle_walk.py` walks every room from its 14 entries: 11085 of 11091 code bytes reached, the rest are dead
`exit` bytes after an `exit` / `return` and one skipped byte in room 15.

## Flow

| op | name | operands | what | |
|---|---|---|---|---|
| 00 | jump | j | | H |
| 01 / 05 | jump_if_equal / jump_if_not_equal | j | on Z | H ✓ (05) |
| 02 / 03 | jump_if_negative / jump_if_positive | j | on N | H |
| 0C / 0D | jump_if_carry / jump_if_no_carry | j | on C: after `compare`, reg >= / < b | H |
| 06 | jump_if_none | j | reg low byte == FF | H |
| 0A / 0B | call / return | j | 8-deep stack; return with an empty stack does nothing | H |
| 54 / 55 | call_if_equal / call_if_not_equal | j | the operand is read either way | H |
| 56 / 57 | return_if_equal / return_if_not_equal | | | H |
| 08 / 09 | loop_start / loop_end | count | count 0 takes reg; loop_end jumps back after loop_start until the count runs out | H |
| 07 | wait | frames | | H ✓ |
| 04 | nop | | also every opcode not listed (2D-2F, 32, 34, 3C-3F, 46-4F, 58-5F, 6F-8F, 93-EF, FA-FE) | H |
| 30 | skip_2 | b, b | skips its operands | H |
| FF | exit | | frees the unit markers (F7), ends the script | H ✓ |

## Register, variables, flags

| op | name | operands | what | |
|---|---|---|---|---|
| 10 | compare | b | reg low vs b | H ✓ |
| 11 | test_bits | b | reg low & b, flags only | H |
| 12 / 13 | increment / decrement | | reg low, flags | H |
| 14 / 15 | add / subtract | b | reg low, flags | H |
| 16 / 17 | load / load_word | b / w | | H |
| 1F | swap_bytes | | reg low <-> high | H |
| 62 / 63 | load_var / store_var | var | $7E:3F90 + var & 7F, a word with bit 7 | H |
| 60 / 61 | set_flag / clear_flag | flag | bit of $7E:3FD0 | H |
| 52 / 53 | jump_if_flag / jump_unless_flag | flag, j | | H ✓ (52) |
| 0E / 0F | jump_if_local_flag / jump_unless_local_flag | flag, j | bit of $1AC0 (area triggers) | H |
| F4 | set_room_flag | b | $7F:C000 + (b & 7F) = FF, or 00 with bit 7 | H ✓ |
| 50 / 51 | jump_if_room_flag / jump_unless_room_flag | flag, j | room flag nonzero / zero | H |
| 18 | load_turn | | reg = $7E:3BD6, the turn number (1 on the first, 2 after the first end of turn) | H ✓ |
| 1E | load_3bd8 | | reg low = $7E:3BD8 (C0:0043 hands it to C0:AE5E; scenario number?) | L |
| 64 | load_event_arg | | reg low = `$1A0C`: `$3D` when entry 08 / 0B / 0C ran, the third operand of 31 | M |
| 65 | load_event_word | | reg = `$1A12` / `$1A13` (C0:08B7, EF:4123 by the entry) | L |
| F2 | load_sound_byte | b | reg low = $7E:1D00 + b (the sound driver's page) | M |

## Units and map

| op | name | operands | what | |
|---|---|---|---|---|
| 19 | load_current_unit | | reg low = `$B1` | H |
| 1D | select_unit | unit | unit (FF: `$1A0E`) on the map → current, camera on it, 32 frames; reg = unit, or FF | H ✓ |
| 1C | select_unit_reg | | select_unit with reg low | H |
| 3A | check_unit | unit | reg = unit if on the map, else FF | H |
| 1A | load_unit_field | offset | reg low = byte `offset` of the current unit's record | H |
| 91 | load_unit_byte | unit, offset | same for `unit`; an invalid unit ends the script | H |
| 90 | load_unit_position | unit | reg = x, y (FF FF without the unit) | H |
| 1B | find_member_slot | b | reg = slot 0-11 whose 4 bytes at +3 (7E:2B53) hold b, else FF; b FF = reg | M (slot = squad: L) |
| 36 | grab_unit | | the current unit follows the cursor | M ✓ |
| 35 | move_cursor | b | bits 6-7 direction (00 / 40 / 80 / C0 → 8 / 4 / 2 / 1), bits 0-5 steps, animated | M ✓ |
| 37 | drop_unit | | the unit takes the cursor position, map occupancy updated | M ✓ |
| 31 | move_cursor_to | x, y, arg | cursor to x, y step by step; then `$3D` = `$1A0C` = arg and C0:C1E0, 472D, 469F, CBA8, 44FF, 966D, 93EF run (an action at the cursor?) | M (move) L (rest) ✓ |
| 38 | unit_walk_off | dir | grab, walk in direction `dir` (4 bits) until off the edge, then remove_unit | M |
| 39 | remove_unit | | the current unit off the map (record bit 7) | M |
| 3B | spawn_unit | flags | enemy unit 0C + (var 3B & F): bit 7 sets it up from vars 39-3B (EF:0070), bit 6 keeps its position (else vars 3C / 3D), bit 5 tries the 3x3 then 5x5 around a blocked tile, bit 4 skips the tile check; reg = unit or FF | M |
| 33 | set_enemy_order | unit, value | enemy unit (0C-1B) record +0x10 = value; reg 0, or FF | L (meaning of +0x10) |
| 42 | focus_unit | | camera on the current unit (C0:A39E) | M ✓ |
| 43 | scroll_view | dir, steps | dir 8 / 4 / 2 / 1 as `$9F`, steps & 3F | M ✓ |
| 44 / 45 | shake_screen / stop_shake | b / | `$1A1E`: bits 0-4 amplitude, bit 7 x (random), bit 6 y (C0:5DFE) | M |
| 66 | test_area_units | x, y, w, h | Z = no unit in the rectangle (map $7E:8001) | M |
| 67 | test_unit_tile | unit | flags from the map byte +1 under the unit | L |
| 68 | load_tile_unit | x, y | reg = map byte at x, y (FF = reg); flags from its bit 5 | M |
| 69 | test_unit_area | x, y, unit | walks the map from x, y for `unit` (C0:4B05); reg = a count, 80 or FF | L |
| 6A | test_area_terrain | x, y, w, h | ORs / ANDs terrain bits 1-2 over the rectangle; reg 0 / 1 / 80, FF out of the map | L |
| 6B | load_terrain | x, y | reg = terrain of the tile (7E:6E00 / 7E:7E00); x bit 6: the tile under unit y | L |
| 6C | test_unit_area_vars | | 69 with vars 3C, 3D, 3A | L |
| 6D | test_area_terrain_vars | | 6A with vars 3C-3F | L |
| 92 | find_enemy_flag_4 | | reg = first enemy unit whose record has bit 2 (C0:60C9), else FF | M |
| 6E | queue_scripted_action | 7 bytes | vars 28-2E: action (`$3D`), `$81`, `$89`, ?, scroll bits, kind, name index (C7:0038). C0:5F36 plays it when an enemy unit has flag 4. Room 7 uses it (its texts talk of cannons) | M |
| F0 | map_event | n | redraw, then toggle room flag of map event n ($7F:C282) and apply its tiles | M ✓ |
| F5 | map_event_f5 | n | the same without the redraw first, `$1A62` = FF | L |
| F6 | refresh_map | | C0:4047 alone | L |
| F7 | unit_marker | unit, kind | takes a slot of 8 (`$1A68`) for the unit, C0:859B draws kind (C6:B400); freed by exit | L |
| F8 / F9 | set_unit_sprite / restore_unit_sprite | unit, value / unit | record +8 saved to +0x1C and set / put back, sprite refreshed (C0:6725) | L |
| F3 | give_item | item, count | adds to the inventory ($7E:3AD0, max 99), shows the item line | M |
| F1 | sound_command | 4 bytes | to $7E:1D00, jsl C3:0000 (sound driver, talks to $2140) | M |
| 40 / 41 | set_mode_10 / clear_mode_10 | | `$1A05` bit 4 (C0:EB65 skips its work while set) | L ✓ (40) |

## Text

Texts are copied to $7E:C000 (0xE0 bytes, `copy_battle_text`) and shown by `display_battle_text` +
`battle_string_manip`.

| op | name | operands | what | |
|---|---|---|---|---|
| 20 | open_window | | message window; `$F7` = 1 when `$93` >= 0B, else A0 (placement / style) | M ✓ |
| 21 / 25 | open_window_1 / open_window_a0 | | `$F7` = 1 / A0 | M |
| 22 | close_window | | | M ✓ |
| 24 | clear_window | | clears 7E:D000-DFFF, DMAs it to VRAM 4180 | M ✓ |
| 26 | say | t | copy + show | H ✓ |
| 23 | say_index | i | text i of the text table, copy + show | H |
| 29 / 28 | load_text / load_text_index | t / i | copy only | H |
| 2A | set_text_arg | n, b | the argument of the n-th control code (F4-F8, FA, FC; F9 takes a word) of the loaded text = b; n bit 7: reg instead | M |
| 2B | set_text_arg_word | n, w | the same with a word | M |
| 2C | say_loaded | | show the loaded text | H |
| 27 | ask | t | copies 0x20 bytes at t to $0720, draws them, runs a choice (C0:37F7); its flags land in `$1A04` | M |

## Not verified

Unused by the vanilla scripts (decoded from the handlers only): 0C, 0D, 11, 14, 15, 17, 1A, 1E, 21, 23, 27-2C, 30,
55-57, 67, 69, 6D, 91, F2, F7-F9. Untested in game: every opcode without ✓.

The FR text in `text/fr/battle/0007.xml` still has a ref at 0x174 from the old walk, which read 6E as one byte: the
build rewrites bytes 0x174-0x175 of `queue_scripted_action`'s operands (01 32 → the end-of-texts pointer). In
`0015.xml` the `say` at 0xFB (ref 0xFC) is missing while the base moved to its text (0x133), so it shows the first
French text.
