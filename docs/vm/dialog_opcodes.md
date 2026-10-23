# Dialog room opcodes

The field's script VM: the runner at DA3F00 (`opcode_runner`), its handlers in the word table DA3F20, indexed by the
opcode. `utils.vm.opcodes_map.opcode_names` names them, `utils.vm.room_ops.OPERANDS` gives their operands,
`utils.vm.room_walk` walks every room from its entry points. Handlers are labelled `op_<name>` in both kintsuki
projects (`bl.kintsuki`, `Bahamut Lagoon (J) [!].kintsuki`).

`uv run python -m utils.vm.room_script ROOM [--fr] [--bytes]` lists a room: its header entries, then every byte as
an instruction (with `L` labels on jump targets and entries, a text operand showing its text) or data (header
tables, texts, palettes, bytes no entry reaches). `utils.vm.room_asm` encodes instructions back to their bytes (all
83 rooms re-encode exactly) and assembles scripts with labels from Python, as `tests/test_room_opcodes.py` does.

Confidence: **H** handler read fully and what it drives is clear, **M** mechanism clear, its meaning partly, **L**
what the RAM it writes does is a guess (named after the RAM). **✓** reproduced in game by `tests/test_room_opcodes.py`.
*uses*: instructions reached in the 83 script rooms of the Japanese ROM.

## Format

**Storage.** Room n: 24-bit pointer at DA8000 + 3n; bit n of the DA8300 bitmap says LZ-compressed (`u16` size, then
the LZ blocks, `utils.dump_rooms.decompress_block`). The 83 compressed rooms are the scripted ones; the field
decompresses the room to its buffer (`$7F:A000` for room 0) and keeps a long pointer to it in `$67`.

**Addresses.** Every address in a room (header words, jumps, text and data pointers) is an offset from the room's
start. The script PC is `$6A`.

**Header.** Words, as long as word 0 says (8 in 71 rooms, then 0x0C, 0x0A, 0x0E, 2):

| word | what | runs when |
|---|---|---|
| +0 | start-up script; its offset is the header's length | the room loads (`room_entry_point`) |
| +2 | actors: offsets of 7-byte actor records, FFFF ends (at most 0x17) | |
| +4 | position triggers: (x, y, flags, script) 5-byte records, FFFF ends | the player steps on the tile, or presses A facing it (`walk_room_4`): flags bit 0 skips the step, bit 1 the A press |
| +6 | actor events: a script per actor id, FFFF ends | A on the actor (`$0324`, `$3D` bit 2), or touching it when its `$7E:B800` bit 2 is set (`$0322`, `$3D` bit 0, opcode 17) |
| +8 | timer script | the opcode 40 countdown reaches 0 while the timer (41) runs |
| +A | area triggers: (x1, y1, x2, y2, flags, script) 7-byte records, FFFF ends | as +4, on the box's edge, while opcode 60 enables them (`walk_room_a`) |
| +C | skip script | Start, once opcode 7C allows it (DA0566 sets `$41` bit 4) |

The field loop (DA043C) starts these only while no script runs (`$3F` bit 0); each runs to its FF.

**Runner.** `opcode_runner` reads the opcode at `[$67] + $6A`: FF returns carry set (the script is over), else it
calls the handler with Y = the PC and adds what the handler returns in A to `$6A` (0 when it jumped). Handlers read
their operands with `iny : lda [$67],y`. 95-9F are bare `sep #$20 : rts`: A still holds (opcode * 2) & 0xFF, so
they skip 0x2A-0x3E bytes; A0-FE index past the table. No room uses either.

Handlers that wait (3F, 47, 48, 8A, 8C, the choices, the window opcodes) loop on `sick_call` (DA0581), which runs
the 32 tasks enabled in `$36`-`$39` (addresses at `$033B`) through pushed return addresses (README, "Strange
Calling Convention"): one tick, so the field keeps animating while the script waits.

**Operands.** Bytes unless marked: `.w` a word, `.l` a 24-bit address (word, bank). `addr` is a script address,
`text` a text pointer (a string up to its end, FD or FF, as `utils.vm.opcodes.get_string_from_room` reads it), `data` a pointer to room data.

- Event flags: `$7E:3D30` bit array, flag n is bit n & 7 of byte n >> 3 (set_flag, jump_if_flag, store_actor_facing).
- Room bits: `$0312`, zeroed when a room loads (set_room_bits, jump_if_room_bits).
- Actor n: script record `$7E:B800 + n * 0x80`, sprite object `$0700 + n * 0x10` (x `$0704`, y `$0702` in px from
  the camera at `$037C` / `$037E`). Map coordinates are 16 px tiles.
- Palette operand (`first, count`, read by DA4ACC): colours first..first+count-1; first FF = colours 0, 10-7F,
  90-FF, FE = 0, 10-7F, FD = 90-FF (count then ignored).
- Variables (56, 57, 58, 82, 90): `table, record, field`, see set_var.

## Opcodes

### Flow, flags, room bits

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 00 | jump | addr | `$6A` = addr | 594 | H |
| 01 | jump_if_room_bits | mask, addr | jump if `$0312 & mask` (room bits) | 0 | H |
| 02 | jump_unless_room_bits | mask, addr | jump if `$0312 & mask` is 0 | 0 | H |
| 03 | jump_if_flag | flag, addr | jump if the event flag is set (`$7E:3D30` bit array, flag >> 3 its byte) | 1580 | H |
| 04 | jump_unless_flag | flag, addr | jump if it is clear | 460 | H |
| 05 | call | addr | push PC + 3 (8 deep: count `$097B`, words `$097C`); a full stack skips the call | 1597 | H |
| 06 | return |  | pop; an empty stack falls through | 409 | H |
| 07 | jump_if_item | item, addr | jump if the inventory (`$7E:3AD0`, 128 item / count pairs) holds one | 0 | H |
| 0A | loop_start | count.w | push a loop (8 deep, `$098C`): count, then PC + 3; FFFF loops forever | 132 | H |
| 0B | loop_end |  | count - 1; back to the loop start until 0, then pop | 132 | H |
| 0C | set_flag | flag | set the event flag | 753 | H |
| 0D | clear_flag | flag | clear it | 237 | H |
| 3F | wait_frames | frames | wait (0 = 256), the tasks running meanwhile | 3230 | H |
| 50 | random_branch | a, b | step the RNG (`$7B`): bit 0 clear jumps to a, set to b; never falls through | 96 | H |
| 62 | set_room_bits | mask | `$0312 |= mask`: room bits, zeroed when a room loads | 1 | H ✓ |
| 63 | clear_room_bits | mask | `$0312 &= ~mask` | 0 | H |
| 70 | jump_if_actor_in_area | actor, x1, y1, x2, y2, addr | jump if the actor's 16 px tile is in the box, bounds included | 1 | H |
| 8C | wait_frames_long | frames.w | wait | 30 | H |
| 8D | jump_if_pad | which, mask.w, addr | jump if a pad bit of mask is set (0: `$53`, else `$55`, the word DA2D78 reads A in) | 14 | H |
| 94 | jump_if_actors_near | actor, actor, addr | jump if the two are less than 16 px apart on each axis | 0 | H |
| FF | exit |  | the runner stops (carry set): the script ends | 2225 | H ✓ |

### Variables and memory

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 56 | set_var | table, record, field, value | byte = value. Tables: 0 `$7E:2100 + r * 0x40` (units), 1 `$7E:2CD0 + r * 0x30`, 2 `$7E:2B50 + r * 0x20` (parties, see 81), 3 `$7E:38D0 + r * 0x20`, 4 `$7E:3BD0 + field` (record ignored), 5 `$7E:3BF0 + r * 0x20`, 6 `$7E:(record + field * 0x100)`; above 6 = table 0 | 200 | H |
| 57 | or_var | same | `|=` | 1 | H |
| 58 | and_var | same | `&=` | 2 | H |
| 59 | copy_byte | src.l, dst.l | copy one byte | 67 | H |
| 64 | dma_to_vram | src.l, vram.w, size.w | DMA to VRAM through task 1B; waits for it | 0 | M |
| 65 | lz_decompress | src.l, dst.l | LZ decompress (DA2BFA, the room format) | 0 | H |
| 68 | copy_block | src.l, dst.l, length.w | copy a block (DA2549) | 0 | M |
| 82 | add_var | same | `+=`, 8-bit wrap | 1 | H |
| 90 | add_var_clamped | table, record, field, delta, min, max | `+=` then clamp to [min, max]; tables 0-5 only | 0 | H ✓ |

### Party, items, money

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 39 | give_item | item | +1 (cap 99), a free slot when absent | 118 | H |
| 3A | take_item | item | -1 (floor 0) | 0 | H |
| 3B | restore_hp | unit | `$7E:D665 = $7E:D667` (unit * 0x40): HP to max | 0 | M |
| 3C | restore_mp | unit | `$7E:D669 = $7E:D66B`: MP to max | 0 | M |
| 3D | add_money | amount.w | money (`$7E:3BD3`, 24-bit) +, saturates at FFFFFF | 2 | H |
| 3E | remove_money | amount.w | money -, floor 0 | 4 | H |
| 80 | setup_unit_80 | id | C7 record (DA2558, Y = 8): `+0E` to `$7E:D76E`, `+0D` bit 7 to `$7E:D76D`, three loaders | 20 | L |
| 81 | select_units_81 | party | fill the party's 4 member slots (`$7E:2B53 + p * 0x20`) with the first units 0-1F present (`$7E:2100` record not FF, bit 0 set, bit 1 clear) that DA6C93 accepts | 2 | M |
| 91 | call_ef0080 | flag | of flags flag..flag+5, the indices of the first two set go to `$7E:2000`; with two, `jsl EF0080` | 1 | L |

### Actors and sprite objects

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 0E | actor_set_frame | actor, frame | sprite frame (`$070D`, DA0F52) and `$7E:B801` bit 5: the walk tick (DA2075) then leaves the frame alone, walking or not | 2774 | H ✓ |
| 0F | actor_set_speed | actor, speed | `$7E:B808`, step table at `$7E:B840` (DA17FD); the player's also in `$0321` | 1001 | H |
| 10 | actor_set_anim_rate | actor, value | `$070C` (4 at load), taken off the current cel's timer (`$0709`) every frame (DA70A9): the animation's speed | 649 | H |
| 11 | set_player_actor | actor | the controlled actor (`$0320`) | 165 | H |
| 12 | actor_place | actor, x, y | place on a tile (signed, 16 px, from the map's corner) and show | 2697 | H |
| 13 | actor_move | actor, steps…, FF / FE | walk (DA1708 steps it): a step byte is direction (high nibble: 0 up, 1 down, 2 left, 3 right; 4-7 diagonals, not run) and tiles (low; 0 only turns, 5 frames); FC waits 60 frames, FD walks 15 tiles a random way, FF ends the walk (`$7E:B801` bit 6), FE starts the list over. The list goes to `$7E:B820` | 5322 | H ✓ |
| 14 | actors_hold | actors…, FF | for each, wait for its step to end, then `$7E:B801` bit 1 stops its walk on that tile (DA1E8A) | 31 | H ✓ |
| 15 | set_follower | actor, distance | the actor follows the player (`$0323`); 0 detaches | 7 | M |
| 16 | actor_set_animated | actor, on | 0 sets `$7E:B801` bit 5 (the walk keeps the frame it has), else clears it (the walk sets its frames) | 1381 | H ✓ |
| 17 | actor_set_behavior | actor, value | `$7E:B800`: bit 1 walks through the map's collision and the 55 box (DA1F5D), bit 2 makes touching the actor run its +6 event (DA1EC4) | 469 | H ✓ |
| 18 | actors_release | actors…, FF | bit 1 off: the held walks go on | 36 | H ✓ |
| 19 | actor_set_palette | actor, palette | OBJ palette (`$0707` bits 0-2); FF the sprite's default (DA7B50) | 42 | H |
| 1A | store_actor_facing | actor, flag | clear flags flag..flag+3, set flag + the actor's facing | 99 | H |
| 21 | actor_set_layer | actor, mode | `$0707` bits 5-6: 1 bit 6, 3 bit 5, else neither; rebuilds the OAM | 123 | L |
| 27 | scroll_camera_to_actor | actor, speed | scroll the camera to centre the actor | 160 | H |
| 47 | wait_actor_animation | actor | clear `$0706` bit 2, wait until the cel animation sets it, on its last cel (DA70DA) | 499 | H |
| 48 | wait_actor_move | actor | wait until the walk reaches its FF (`$7E:B801` bit 6); never returns for an FE list or a walk a wall stops | 2258 | H ✓ |
| 4C | actor_sprite_offset | actor, dx, dy | sprite offset: signed px added to its screen x (`$7E:B812`) and y (`$7E:B811`) when drawn (DA6FFC) | 264 | H ✓ |
| 4D | actor_set_facing | actor, direction | facing 0-3 (`$0707` bits 3-4) | 116 | H |
| 53 | save_actor_position | actor, slot | save its map position to `$04A0 + slot * 4` (slot < 0x18) | 196 | H |
| 54 | restore_actor_position | actor, slot | put it back there, shown | 204 | H |
| 55 | actor_walk_box | actor, x1, y1, x2, y2 | walk box: tiles [x1, x2) x [y1, y2) (`$7E:B813`-`$7E:B816`, 0, 0, 80, 80 at load) a pad step may not leave (DA53D2); a scripted walk was only seen stopped on its first step | 69 | H ✓ |
| 66 | object_create | slot, frame, x, y, attr, size, f | raw sprite object: `$0700` = 1, `$0701`, `$0704`, `$0702` (px), `$0707`, `$070A`, `$070F` | 0 | M |
| 67 | object_remove | slot | remove it | 0 | M |
| 83 | actor_place_83 | actor, x, y | as 12, then DA6F63 (draws it now) instead of DA0F58 when DA432A returns carry clear | 82 | L |
| 88 | call_da781c | id | load animation id (C7 table at C7002C) into the `$7E:FA00` slots, which 22 and 89 run | 8 | M |
| 8A | wait_object | slot | wait until the slot's `$7E:FA00` animation is done | 1 | L |
| 8F | actor_set_sprite_frame | actor, frame | `$0701` and `$070D`, stops the auto-animation | 4 | M |

### Map, camera, layers

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 1B | load_map | map | clear the camera state (`$037C`-`$03D3`), load the map | 268 | H |
| 1C | set_camera | x, y | camera at a tile (16 px), redraws | 341 | H |
| 1D | scroll_camera | x, y, frames | scroll the camera to a tile in `frames` frames (straight, from the script's 3rd frame); the script goes on meanwhile | 69 | H ✓ |
| 1E | layer_motion_1 | a, b, word | motion slot 1 (`$03B6`, `$03B8`, `$03C2`) | 124 | L |
| 1F | layer_motion_2 | a, b, word | slot 2 (`$03BA`, `$03BC`, `$03C4`) | 55 | L |
| 20 | layer_motion_3 | a, b, word | slot 3 (`$03BE`, `$03C0`, `$03C6`) | 0 | L |
| 24 | map_set_tile_bg1 | x, y, tile.w | BG1 map tile (tile & 0x9FF), redraws it if on screen | 959 | M |
| 25 | map_set_tile_bg2 | x, y, tile.w | BG2 (tile & 0x8FF) | 50 | M |
| 26 | map_set_attribute | x, y, attribute | collision attribute (& 0x17) in `$7E:6801` | 13 | M |
| 4E | set_tile_priority_a | on | `$032C` = 0 / 0x2000; clears the priority bit over `$7E:A800` | 4 | L |
| 4F | set_tile_priority_b | on | same with `$032E` | 4 | L |
| 7D | layer_velocity_a | dx, dy | signed velocity `$0398` / `$039A` | 76 | L |
| 7E | layer_velocity_b | dx, dy | signed velocity `$039C` / `$039E` | 12 | L |
| 7F | camera_limit | x, y | camera limits: its largest x, y (`$0394` / `$0396` = tile * 16, 6 bits), which the player's walk clamps the camera to (DA2FE1) | 74 | H ✓ |
| 84 | call_da748f |  | E8:CD55 (0x400) to `$7E:E000`, builds 0x800 bytes at `$7E:E400`, DMA to VRAM 3040, then 87 | 1 | L |
| 87 | call_da755c |  | fill the `$7E:6000` tilemap buffer with 0x2008 | 22 | M |
| 8B | toggle_8b | mode | HDMA channel 6 to BG3HOFS from `$7E:D790`: 0 one band, else several (DA75D8) | 2 | L |
| 93 | set_map_priority | on | priority bit (0x20) over the `$7E:6001` tilemap | 1 | L |

### Screen, palettes, windows

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 23 | layer_bg1 | main, sub | BG1 on the main / sub screen (`$6F` / `$70` bit 0) | 87 | H |
| 29 | set_screen | on | 0 forced blank, else display | 739 | H |
| 2A | fade_brightness | from, to, speed, ? | brightness fade (`$3E` bit 4); the 4th operand `$09AD`: L | 664 | H |
| 2B | set_brightness | level | brightness, stops a fade | 0 | H |
| 2C | fade_mosaic | from, to, speed, layers | mosaic fade | 21 | M |
| 2D | set_mosaic | size, layers | mosaic | 6 | M |
| 2E | color_effect | 9 bytes | colour math / fixed colour fade (`$71`, `$09D8`-`$09E0`, `$0338`-`$033A`) | 162 | L |
| 2F | palette_fade_uniform | first, count, time, repeat, from, to | palette fade: R, G and B each offset (signed, added) from `from` to `to` over `time` (0 at once, 8 about 20 frames, 32 about 70); repeat 1 starts over at the end; the script goes on | 515 | H ✓ |
| 30 | palette_fade_rgb | first, count, time, repeat, 6 bytes | same, `from, to` for R, G, then B | 152 | H ✓ |
| 31 | palette_restore | first, count, a | palette restore (DA5D24) | 7 | L |
| 32 | palette_effect_32 | first, count, a, b | palette effect (DA5C75) | 1 | L |
| 33 | palette_effect_33 | first, count, on | same, `$09BF` = 0 when on, else 4 | 26 | L |
| 49 | palette_commit | first, count | copy working colours `$7E:C400` to `$7E:C600`; FF / FE / FD presets. CGRAM did not follow within 5 frames in game: what uploads `$7E:C600` is not traced | 100 | M |
| 4A | layer_bg2 | main, sub | BG2 (bit 1) | 89 | H |
| 4B | layer_bg3 | main, sub | BG3 (bit 2) | 124 | H |
| 51 | load_palette | first, count, data | colours from room data (a room offset) | 13 | H |
| 52 | layer_obj | main, sub | OBJ (bit 4) | 83 | H |
| 5B | setup_windows | 12 bytes | window registers: W12SEL, W34SEL, WOBJSEL, 4 positions (`$09E1`), WBGLOG, WOBJLOG, TMW, TSW, CGWSEL | 15 | M |
| 5C | load_graphics_5c | id | `jsl C2001C` (graphics id) into `$7F:E700` / `$7F:E800` / `$7F:F800` | 15 | L |
| 5D | animate_window_1 | 6 bytes | window 1 animation (`$40` bit 1) | 18 | L |
| 5E | animate_window_2 | 6 bytes | window 2 animation (`$40` bit 2) | 2 | L |
| 72 | start_effect_task | a, b, c, d.w, e.w, f | start task 11 (DA33CA) with `$0A49`-`$0A5D` | 12 | L |
| 74 | window_1 | on | window 1 animation: 0 on, else off and reset | 1 | L |
| 75 | window_2 | on | same for window 2 | 0 | L |
| 76 | windows_off |  | both windows off, window registers reset | 9 | M |
| 77 | effect_77 | 5 bytes | effect at `$09FB`-`$0A00`, `$41` bit 0 | 9 | L |
| 78 | effect_78 | 5 bytes | effect at `$0A01`-`$0A06`, `$41` bit 1 | 4 | L |
| 79 | stop_effect_task |  | stop task 11 | 5 | M |
| 86 | refresh_3b_40 |  | `$3B` bit 6, one tick | 36 | L |

### Text windows

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 08 | yes_no | text, yes, no | prompt, cursor on 2 lines; A jumps to the line's address, B falls through | 194 | H |
| 09 | multiple_choice | text, a, b, c | same with 3 lines (the `$0964` cursor 0-2); B falls through | 47 | H |
| 34 | set_window_position | row, height | window `$0330` / `$0332`; height in tile rows, two a line (utils.dump_rooms.WindowHeights) | 538 | M |
| 35 | open_window | style | open the window: style not 0 draws its frame (tiles 00-03, flipped at the corners) in the `$7E:4000` tilemap, `$0332` rows high; 0 opens it frameless (`$3F` bit 1). `$3E` bit 1 while open | 2993 | H |
| 36 | close_window |  | close it | 3292 | H |
| 37 | display_text | text | print text in the window | 3160 | H |
| 38 | clear_window_text |  | clear the window's text, when one is open | 561 | M |
| 7B | display_credit | text | credits text (`$41` bit 2 while it prints) | 18 | M |
| 85 | draw_credit_line | x, y, text | credits line at x, y in the A = 1 alphabet (room 248) | 82 | M |

### Sound

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 6A | sound_reset |  | `jsl C30008` | 0 | L |
| 6B | play_music | a, b | driver command 04 (music) | 144 | M |
| 6C | sound_command_13 | a, b | driver command 13: SPC command 13 when a is not 0, 1B when 0 (C303D0) | 220 | L |
| 6D | play_sound | id | driver command 00, `$1D02` = 0x80 (sound effect) | 1050 | M |
| 6E | sound_command_13_b | a, b | same as 6C | 3 | L |
| 6F | sound_command_12 | a, b | driver command 12: SPC command 12, or 1A when a is 0 | 201 | L |
| 92 | sound_command_11 | a, b | driver command 11: SPC command 11, or 19 when a is 0 | 3 | L |

### Field engine, triggers, system

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 22 | animate_to_wram | on | `$3F` bit 5: runs the `$7E:FA00` animations (88) that copy to WRAM (DA79AA; `$3B` bit 4 after) | 110 | M |
| 28 | camera_follow | on | camera follow: 0 sets `$3C` bit 5, the player's walk no longer scrolls the camera (DA1FF2); else clears it | 65 | H ✓ |
| 40 | set_word_0329 | frames.w | timer countdown (`$0329`); at 0 the field runs the +8 script | 1 | H ✓ |
| 41 | set_state_3c_80 | on | timer on / off (`$3C` bit 7; counts while no script runs) | 1 | H ✓ |
| 42 | player_control | on | 0 freezes the player (`$3C` bit 2) | 930 | H |
| 43 | change_room | room | change room once the script ends (`$0326`, `$3D` bit 7) | 169 | H |
| 44 | set_game_state | 4 bytes | `$0300`-`$0303`, `$3E` bit 3: the field loop jumps to C10000 (battle engine) | 0 | M |
| 45 | set_state_0327 | kind, arg | system call: `$0327` picks a vector of DA054B (EE3000 + 4 * kind, kind 8 EE2FE0), most open menu n (`$05FC`) with arg (`$05FE`) | 168 | M ✓ |
| 46 | set_state_3d_10 |  | leave the field engine (`$3D` bit 4: load_room returns, DA0061) | 18 | M |
| 5A | show_mode7_animation | id | `$0300`, `$40` bit 0: the field loop jumps to D58000 | 44 | M |
| 5F | start_effect_5f | id | `$0301`, `$40` bit 3: jumps to C1000F | 2 | M |
| 60 | set_state_40_20 | on | area triggers (+A table) on / off (`$40` bit 5) | 6 | H |
| 61 | walk_turns_actor | on | `$40` bit 6: a walk step also turns the actor to its direction (`$0707` bits 3-4, DA2342) | 103 | M |
| 69 | set_bits_3b | mask | `$3B |= mask` | 0 | L |
| 71 | set_state_40_80 | on | `$40` bit 7 | 0 | L |
| 73 | set_state_42 | value | `$42`; its readers test bits 0 (skips the BG2 scroll update, DA308C), 2 and 4-7 (DA28AD-DA2F02) | 91 | L |
| 7A | start_effect_7a | a, b, c, d, id | `$7E:FFF0`-`$7E:FFF3`, then as 5F | 137 | M |
| 7C | set_state_41_08 | on | Start runs the +C script (`$41` bit 3): the skip | 1 | H ✓ |
| 89 | animate_to_vram | on | `$41` bit 5: runs the `$7E:FA00` animations (88) that queue a VRAM DMA (DA79BB, the `$0A11` queue) | 28 | M |
| 8E | camera_ignore_limit | on | `$41` bit 6: the followed camera ignores the 7F limits (DA2FE5) | 4 | H ✓ |

## Coverage

`uv run python -m utils.vm.room_walk` walks each script room from all its entry points (the header table above),
following every jump, call and branch; it counts the header, its tables, the actor records, every reached
instruction and the texts and palette data they point at. It reaches **310 938 of 314 381 bytes (98.9 %)** of the
83 rooms, and every opcode the round-trip disassembler (`utils.disasm`) walks.

The 3 443 bytes left are 469 ranges:

- 321 single bytes: 164 FE right after a text's FD end, 156 FF after a jump, return or random_branch (padding the
  disassembler used to read as code after random_branch, which never falls through).
- 226 ranges decode end to end as instructions (1 606 bytes): dead code, mostly 33-byte blocks repeated
  (`unreached 156e-158e (33 bytes), decodes as 8 ops`) that no header entry or jump reaches. Some may run from
  another room's script or a trigger the walk does not know: L.
- the rest do not decode: data nothing points to, or texts whose pointer sits in dead code.

Lowest: room 216 (86.5 %), 214 (88.4 %), 100 (93.8 %). Opcodes no room uses: 01 02 07 20 2B 3A-3C 44 63-69 71 75 90
94 (they are read from their handlers alone).

## Not checked

The ✓ rows are the only ones run in game. The text terminator (FD, a single FE after it) is the text dumper's
reading, not checked against `display_dialog_string`. The L rows name RAM nothing here traced further: who reads
`$40` bit 7, `$41` bits 0-1, `$42` (readers found, not followed), `$09AD`; the colour math of 2E-33 and 77-78, the
window animations (5D, 5E, 74, 75) and the SPC side of the sound commands (6C, 6E, 6F, 92) are not read. Motion
steps 4x-7x (diagonals) and FB (a 30-frame wait the step code has, never traced) no room was seen to run. Of the
actor record, `$7E:B800` bits 0 and 3-7 and `$7E:B801` bits 2-4 and 7 are only partly read (walking, player).
