# Bahamut Lagoon room opcodes

Read from the field VM handlers in bank DA (`opcode_runner` DA3F00, `opcode_table` DA3F20, one word per opcode
00-9F). `utils/vm/opcodes_map.py` carries the names and lengths below; `generate_macros.py` turns them into
`src/room_macros.s`.

## How the VM runs

- The script PC is `$6A` (room-relative), the room base `[$67]` (decompressed rooms live at 7F:A000).
- `FF` ends the script. Otherwise X = opcode × 2 and the runner calls the handler.
- **A handler returns its own length in A**: the runner adds it to `$6A`. A jump writes `$6A` itself and returns 0.
  Every length below is the handler's `lda #n` before `rts`, so lengths are exact, not inferred from rooms.
- Opcodes 95-9F are `sep #$20; rts` stubs: they return garbage as a length, no room uses them.

## Room header (`room_entry_point` DA14F1 and `room_02`…`room_0C`)

The entry word doubles as the header length: slots at or past it are absent.

| Offset | Run when | Contents |
|---|---|---|
| 00 | the room loads (`room_entry_point`) | entry script |
| 02 | | actor table: words to 7-byte actor entries, `FFFF` ends, at most 0x17 |
| 04 | A is pressed facing a tile (`room_04`, `$3D` bit 3) | 5-byte entries: tile x, y, mode, script. Mode bit 1 set = not examinable |
| 06 | A is pressed facing an actor (`room_player_events`, `$0324`), or an actor whose behaviour has bit 2 walks into the player (`room_06`, `$0322`) | word table of scripts, one per actor |
| 08 | the timer runs out (`room_08`, `$3D` bit 1): op 40 sets the frame count, op 41 starts it | script |
| 0A | A is pressed facing the edge of a box, while op 60 has enabled it (`room_0A`, `$40` bit 4) | 7-byte entries: x1, y1, x2, y2, mode, script |
| 0C | START is pressed, once op 7C has enabled it (`room_0C`, `$41` bit 4) | script |

The A-button checks need player control (`$3C` bit 4, set by 11, cleared while 42 holds control). The faced tile
is the one 16 px ahead along the actor's facing (`DA5049`). The per-frame dispatcher (DA0420-DA054A) also serves
43 (room change), 45 (sub-screen by `$0327`, table DA054B), 46 (leave the field engine) and 5A (`jml D58000`).

Actor entry (`DA15BA`): sprite (F8+ = party slot from 7E2118), palette (FF = the sprite's default from DA7B50),
x and y in tiles, facing (bits 0-1, stored ×8) and flags (bits 6-7), speed (→ 7EB808), behaviour (→ 7EB800:
bit 0 cannot be talked to, bit 2 starts its slot-06 script on contact).

## Coverage

With every jump followed, the walker reaches 98.5% of the 83 compressed rooms' bytes. What stays unreached:
room 248's credit text (op 85), code left after an `exit` or an unconditional jump with nothing pointing at it
(rooms 66 at 0xa8a, 214 at 0x65e, and the repeated `24 …` tile runs in rooms 6, 7, 15, 18, 20, 76), and their
texts. None of it is referenced, so the French build overwriting it changes nothing.

## State the opcodes touch

| Where | What |
|---|---|
| 7E3D30 | event flags: flag n = byte n>>3, bit 1<<(n&7) (`DA1A38` set, `DA1A59` clear, `DA1A7C` test) |
| `$0312` | room bits: a byte mask set and cleared by 62/63, tested by 01/02 |
| 7E3AD0 | inventory: 0x80 (item, count) pairs, counts capped at 99 |
| 7E3BD3 | money, 24-bit, clamped to 0..FFFFFF |
| 7E2100 + n×0x40 | unit records (0x56-0x58, 0x82 and 0x90 also reach 7E2CD0, 7E2B50, 7E38D0, 7E3BD0, 7E3BF0, or any 7E address) |
| 0700 + n×0x10 | sprite objects: 0702/0704 y/x in pixels, 0706-0707 flags, palette (bits 0-2) and facing (bits 3-4) |
| 7EB800 + n×0x80 | actor movement: 00 behaviour, 01 state bits, 05 moving, 07 facing, 08 speed, 0B/0C tile y/x, 20+ move list |
| 037C/037E | camera x/y in pixels |
| `$6F`/`$70` | main/sub screen layer bits, copied into the layer HDMA table at 7ED811 |
| `$1D00`-`$1D02` | sound driver command and arguments (`jsl C30000`) |

## Opcodes

Confidence: **H** the handler leaves no doubt, **M** the effect is clear but its game meaning is inferred,
**L** only the RAM it writes is known (the name says so: `set_state_3c_20` sets bit $20 of `$3C`).

### Flow

| Op | Name | Len | Operands | Effect | |
|---|---|---|---|---|---|
| 00 | jump | 3 | addr | `$6A` = addr | H |
| 01 | jump_if_room_bits | 4 | mask, addr | jump if `mask & $0312` | H |
| 02 | jump_unless_room_bits | 4 | mask, addr | jump if not | H |
| 03 | jump_if_flag | 4 | flag, addr | jump if event flag set (a jump, not a call) | H |
| 04 | jump_unless_flag | 4 | flag, addr | jump if clear | H |
| 05 | call | 3 | addr | push PC+3 on the 8-deep stack at `$097C` | H |
| 06 | return | 1 | | pop | H |
| 07 | jump_if_item | 4 | item, addr | jump if the inventory holds the item | H |
| 0A | loop_start | 3 | count (word) | push a loop (stack at `$098C`); count FFFF loops forever | H |
| 0B | loop_end | 1 | | decrement, back to the loop start until 0 | H |
| 50 | random_branch | 5 | addr0, addr1 | steps the RNG (`$7B`), jumps to addr1 if its bit 0 is set | H |
| 70 | jump_if_actor_in_area | 8 | actor, x1, y1, x2, y2, addr | jump if the actor's tile is inside the box | H |
| 8D | jump_if_pad | 6 | which, mask (word), addr | jump if a pad bit in mask is set (0: `$53` new presses, else `$55` held) | H |
| 94 | jump_if_actors_near | 5 | actor, actor, addr | jump if both are within 16 px on each axis | H |

### Dialogue

| Op | Name | Len | Operands | Effect | |
|---|---|---|---|---|---|
| 08 | yes_no | 7 | text, yes, no | question, then jump | H |
| 09 | multiple_choice | 9 | text, addr ×4 | menu, then jump | H |
| 34 | set_window_position | 3 | x, y | `$0330`/`$0332` | H |
| 35 | open_window | 2 | style | 0: no frame (title cards), else framed | M |
| 36 | close_window | 1 | | | H |
| 37 | display_text | 3 | text | | H |
| 38 | clear_window_text | 1 | | clears the text buffer and DMAs it, if a window is open | M |
| 7B | display_credit | 3 | text | | M |
| 85 | draw_credit_line | 5 | x, y, text | credits text in the A=1 alphabet (room 248) | M |

### Flags, items, money, units

| Op | Name | Len | Operands | Effect | |
|---|---|---|---|---|---|
| 0C | set_flag | 2 | flag | | H |
| 0D | clear_flag | 2 | flag | | H |
| 62 | set_room_bits | 2 | mask | `$0312 |= mask` | H |
| 63 | clear_room_bits | 2 | mask | `$0312 &= ~mask` | H |
| 39 | give_item | 2 | item | +1, max 99 | H |
| 3A | take_item | 2 | item | -1 | H |
| 3D | add_money | 3 | amount (word) | | H |
| 3E | remove_money | 3 | amount (word) | | H |
| 3B | restore_hp | 2 | unit | 7ED665 = 7ED667 | M |
| 3C | restore_mp | 2 | unit | 7ED669 = 7ED66B | M |
| 56 | set_var | 5 | table, record, field, value | table 0 = units (7E2100), 1-5 other arrays, 6 = word address in 7E | H |
| 57 | or_var | 5 | same | | H |
| 58 | and_var | 5 | same | | H |
| 82 | add_var | 5 | same | | H |
| 90 | add_var_clamped | 7 | same, then 2 bytes | add, then clamp (`DA76F7`) | M |
| 59 | copy_byte | 7 | src (24-bit), dst (24-bit) | | H |
| 1A | store_actor_facing | 3 | actor, flag | clears flags flag..flag+3, sets flag + facing | H |
| 91 | call_ef0080 | 2 | flag | collects set flags among flag..flag+5 into 7E2000; with two, `jsl EF0080` | L |

### Actors and sprites

| Op | Name | Len | Operands | Effect | |
|---|---|---|---|---|---|
| 0E | actor_set_frame | 3 | actor, frame | sprite frame (070D), stops auto-animation | M |
| 0F | actor_set_speed | 3 | actor, speed | 7EB808 and the per-step table at 7EB840 | H |
| 10 | actor_set_anim_rate | 3 | actor, value | 070C (4 at load) | L |
| 11 | set_player_actor | 2 | actor | the controlled actor (`$0320`) | H |
| 12 | actor_place | 4 | actor, x, y | tile position, shown | H |
| 13 | actor_move | var | actor, steps…, FE/FF | steps are direction<<4 \| count | H |
| 14 | actors_hold | var | actors…, FF | sets actor state bit 1 | M |
| 18 | actors_release | var | actors…, FF | clears it | M |
| 15 | set_follower | 3 | actor, distance | actor follows the player; 0 detaches | M |
| 16 | actor_set_animated | 3 | actor, on | clears / sets the animation lock (state bit 5) | M |
| 17 | actor_set_behavior | 3 | actor, value | 7EB800 | L |
| 19 | actor_set_palette | 3 | actor, palette | FF = the sprite's default | H |
| 21 | actor_set_layer | 3 | actor, mode | sprite attribute bits 5-6 | L |
| 4C | actor_set_b811 | 4 | actor, a, b | 7EB812, 7EB811 | L |
| 4D | actor_set_facing | 3 | actor, direction | 0-3 | H |
| 55 | actor_set_b813 | 6 | actor, 4 bytes | 7EB813-7EB816 | L |
| 53 | save_actor_position | 3 | actor, slot | slot < 0x18 | H |
| 54 | restore_actor_position | 3 | actor, slot | | H |
| 83 | actor_place_83 | 4 | actor, x, y | like 12, other path when the tile is blocked | L |
| 8F | actor_set_sprite_frame | 3 | actor, frame | 0701 and 070D, stops auto-animation | M |
| 47 | wait_actor_animation | 2 | actor | | M |
| 48 | wait_actor_move | 2 | actor | until the move list is done | M |
| 66 | object_create | 8 | slot, 6 bytes | raw sprite object | M |
| 67 | object_remove | 2 | slot | | M |
| 8A | wait_object | 2 | slot | | L |

### Map, camera, layers

| Op | Name | Len | Operands | Effect | |
|---|---|---|---|---|---|
| 1B | load_map | 2 | map | resets camera state and loads the map | H |
| 1C | set_camera | 3 | x, y | in tiles | H |
| 1D | scroll_camera | 4 | x, y, speed | | M |
| 27 | scroll_camera_to_actor | 3 | actor, speed | | H |
| 1E/1F/20 | layer_motion_1/2/3 | 5 | a, b, word | three parallel motion slots (`$03B6`…`$03C6`) | L |
| 7D/7E | layer_velocity_a/b | 3 | dx, dy (signed) | | L |
| 7F | set_layer_position | 3 | x, y | in tiles | L |
| 24 | map_set_tile_bg1 | 5 | x, y, tile (word) | | M |
| 25 | map_set_tile_bg2 | 5 | x, y, tile (word) | | M |
| 26 | map_set_attribute | 4 | x, y, attribute | collision map 7E6801 | M |
| 23/4A/4B/52 | layer_bg1/bg2/bg3/obj | 3 | main, sub | layer on the main / sub screen | H |
| 4E/4F | set_tile_priority_a/b | 2 | on | | L |
| 93 | set_map_priority | 2 | on | priority bit over 7E6001 | L |

### Screen and palettes

| Op | Name | Len | Operands | Effect | |
|---|---|---|---|---|---|
| 29 | set_screen | 2 | on | forced blank off/on | H |
| 2A | fade_brightness | 5 | from, to, speed, ? | | H |
| 2B | set_brightness | 2 | level | | H |
| 2C | fade_mosaic | 5 | from, to, speed, layers | | M |
| 2D | set_mosaic | 3 | size, layers | | M |
| 2E | color_effect | 10 | 9 bytes | colour math / fixed colour fade | L |
| 2F | palette_fade_uniform | 7 | palette, 5 bytes | | L |
| 30 | palette_fade_rgb | 11 | palette, 9 bytes | | L |
| 31 | palette_restore | 4 | palette, 2 bytes | | L |
| 32/33 | palette_effect_32/33 | 5 / 4 | palette, … | | L |
| 49 | palette_commit | 3 | first, count (FF/FE/FD presets) | copies working colours 7EC400 to 7EC600 | M |
| 51 | load_palette | 5 | palette, data | colours from room data | H |
| 5B | setup_windows | 13 | 12 bytes | window and colour math registers | M |
| 5D/5E | animate_window_1/2 | 7 | 6 bytes | | L |
| 74/75 | window_1/2 | 2 | on | | L |
| 76 | windows_off | 1 | | | M |

### Sound

| Op | Name | Len | Operands | Effect | |
|---|---|---|---|---|---|
| 6A | sound_reset | 1 | | `jsl C30008` | L |
| 6B | play_music | 3 | a, b | driver command 04 | M |
| 6C/6E | sound_command_13(_b) | 3 | a, b | driver command 13 (both handlers are identical) | L |
| 6D | play_sound | 2 | id | driver command 00 | M |
| 6F | sound_command_12 | 3 | a, b | driver command 12 | L |
| 92 | sound_command_11 | 3 | a, b | driver command 11 | L |

### System, transfers, scenes

| Op | Name | Len | Operands | Effect | |
|---|---|---|---|---|---|
| 3F | wait_frames | 2 | frames | | H |
| 8C | wait_frames_long | 3 | frames (word) | | H |
| 42 | player_control | 2 | on | | H |
| 43 | change_room | 2 | room | | H |
| 44 | set_game_state | 5 | 4 bytes | `$0300`-`$0303` | L |
| 5A | show_mode7_animation | 2 | id | `$0300`, `$40` bit 0 | L |
| 5F | start_effect_5f | 2 | id | `$0301`, `$40` bit 3 | L |
| 7A | start_effect_7a | 6 | 4 bytes, id | 7EFFF0-7EFFF3, then like 5F | L |
| 64 | dma_to_vram | 8 | src (24-bit), vram, size | queued through task 1B, waits | M |
| 65 | lz_decompress | 7 | src (24-bit), dst (24-bit) | | H |
| 68 | copy_block | 9 | src, dst (24-bit), length | | M |
| 5C | load_graphics_5c | 2 | id | `jsl C2001C` into 7FE700 | L |
| 72 | start_effect_task | 9 | 8 bytes | task 11 | L |
| 79 | stop_effect_task | 1 | | | L |
| 77/78 | effect_77/78 | 6 | 5 bytes | `$41` bit 0 / 1 | L |
| 80 | setup_unit_80 | 2 | id | | L |
| 81 | select_units_81 | 2 | id | up to four units into 7E2B53 | L |
| 84/87 | call_da748f / call_da755c | 1 | | | L |
| 86 | refresh_3b_40 | 1 | | `$3B` bit 6, one tick | L |
| 88 | call_da781c | 2 | value | | L |
| 8B | toggle_8b | 2 | which | | L |
| 22/28/41/45/46/60/61/69/71/73/7C/89/8E | set_state_… | | | single RAM bits, named after them | L |
| 40 | set_word_0329 | 3 | word | | L |

## What changed in the tools

- 03 and 04 are plain conditional jumps (03 was walked as a call).
- 07, 70, 8D and 94 are conditional jumps: the walker now follows their targets. 94 was walked as an unconditional
  jump.
- 6A is 1 byte, not 9.
- 14 and 18 are actor lists ended by FF.
- The walker runs header slot 0C.

Room 48: an `8D` pad wait hides 14 texts (0x969-0xcc7) the old walker never reached. They sit above the room's
text base (0x826), so the French build overwrites them while their pointers still aim there.
