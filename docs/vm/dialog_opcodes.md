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
the LZ blocks, DA2BFA). The 83 compressed rooms are the scripted ones; the field decompresses the room to its buffer
(`$7F:A000` for room 0) and keeps a long pointer to it in `$67`. `utils.vm.room_walk.room_data` matches that buffer
for every room; `utils.dump_rooms.decompress_block`, which the build reads the Japanese rooms with, stops each LZ
block a byte early and leaves 54 rooms 1-2 bytes short, their ends garbled (checked against `$7F:A000` after
change_room on every room).

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
`text` a text pointer (a string up to its FF or FD, see Text), `data` a pointer to room data.

- Event flags: `$7E:3D30` bit array, flag n is bit n & 7 of byte n >> 3 (set_flag, jump_if_flag, store_actor_facing).
- Room bits: `$0312`, zeroed when a room loads (set_room_bits, jump_if_room_bits).
- Actor n: script record `$7E:B800 + n * 0x80`, sprite object `$0700 + n * 0x10` (x `$0704`, y `$0702` in px from
  the camera at `$037C` / `$037E`). Map coordinates are 16 px tiles.
- Actor record: `$7E:B800` bit 0 walks through actors (DA1EA6), bit 1 through the map and the 55 box, bit 2 touch
  runs its event; `$7E:B801` bit 0 next step wanted, 1 held (14), 2 the step moves, 3 player-controlled (11, DA186D),
  4 skips the actor collision, 5 frame held (0E, 16), 6 list done, 7 tile check pending; `$7E:B802` bit 0 random
  walk (FD), 1 skips the walk tick, 2 off screen (DA2086); `+04` tiles left, `+05` frame in the tile, `+06` frames a
  tile, `+07` direction, `+08` speed, `+09` list index, `+0A` tile level, `+11` / `+12` sprite offset (4C),
  `+13`-`+16` walk box (55), `+20` the list (13), `+40` the step table.
- Field state: `$3C` bits 0-1 frame counter mod 4 (DA0410), bit 2 player frozen (42), bit 4 player idle, bit 5 camera
  not following (28), bit 7 timer (41); `$3B` the vblank uploads (see 69); `$42` the layer scroll (73).
- Palette operand (`first, count`, read by DA4ACC): colours first..first+count-1; first FF = colours 0, 10-7F,
  90-FF, FE = 0, 10-7F, FD = 90-FF (count then ignored).
- Variables (56, 57, 58, 82, 90): `table, record, field`, see set_var.

**Text.** display_dialog_string (DA3AFE, from 37 through DA559A) reads a string byte by byte:

| byte | what |
|---|---|
| 00-EF | a glyph of the current page (`$0961`, its high byte) |
| F0-F3 | glyph page 0-3 (`$0961`) |
| F4 n, F5 n | a byte operand (DA3BDE, DA3C1E; not followed further) |
| F6-F8 | skipped |
| F9 n.w | a word operand (DA3C4E; not followed further) |
| FA | toggle `$0962` bit 0 |
| FB | clear the window's text, back to line 0 (DA3E43) |
| FC n | print the line so far, wait n ticks (DA0602) |
| FD | print the line, next line (`$7A`), **end** without waiting |
| FE | new line (DA3E1A); the window scrolls when full (DA517E) |
| FF | print the line, wait for a key (DA3EEC: `$55` bit 7, or `$53` bits 4-5), next line, **end** |

So a text ends on its first FF or FD outside an operand (`utils.vm.room_walk.text_length`). The 3 272 texts the
walk reaches all end that way; 170 FD are followed by an FE nothing reads. `utils.vm.opcodes.get_string_from_room`
(the dumper) also swallows the byte after FF / FD when it is FF: 31 texts there take one byte the VM does not read.
`$41` bit 2 (7B) sends the string to the credits printer (DA6F2B) instead.

## Opcodes

### Flow, flags, room bits

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 00 | jump | addr | `$6A` = addr | 595 | H |
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
| FF | exit |  | the runner stops (carry set): the script ends | 2226 | H ✓ |

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
| 13 | actor_move | actor, steps…, FF / FE | walk (DA1708 steps it): a step byte is direction (high nibble: 0 up, 1 down, 2 left, 3 right; 4 up-left, 5 down-right, 6 down-left, 7 up-right, a tile on both axes, DA20D7) and tiles (low; 0 only turns, 5 frames); FB waits 30 frames, FC 60, FD walks 15 tiles a random way, FF ends the walk (`$7E:B801` bit 6), FE starts the list over. The list goes to `$7E:B820` up to its FF / FE (more than 32 bytes would run into `$7E:B840`) | 5322 | H ✓ |
| 14 | actors_hold | actors…, FF | for each, wait for its step to end, then `$7E:B801` bit 1 stops its walk on that tile (DA1E8A) | 31 | H ✓ |
| 15 | set_follower | actor, distance | the actor follows the player (`$0323`); 0 detaches | 7 | M |
| 16 | actor_set_animated | actor, on | 0 sets `$7E:B801` bit 5 (the walk keeps the frame it has), else clears it (the walk sets its frames) | 1381 | H ✓ |
| 17 | actor_set_behavior | actor, value | `$7E:B800`: bit 1 walks through the map's collision and the 55 box (DA1F5D), bit 2 makes touching the actor run its +6 event (DA1EC4) | 469 | H ✓ |
| 18 | actors_release | actors…, FF | bit 1 off: the held walks go on | 36 | H ✓ |
| 19 | actor_set_palette | actor, palette | OBJ palette (`$0707` bits 0-2); FF the sprite's default (DA7B50) | 42 | H |
| 1A | store_actor_facing | actor, flag | clear flags flag..flag+3, set flag + the actor's facing | 99 | H |
| 21 | actor_draw_order | actor, mode | OAM order: 1 sets `$0707` bit 6, the sprite goes last (behind every sprite), 3 bit 5, first (in front), else neither (sorted by depth); rebuilds the OAM | 123 | H ✓ |
| 27 | scroll_camera_to_actor | actor, speed | scroll the camera to centre the actor | 160 | H |
| 47 | wait_actor_animation | actor | clear `$0706` bit 2, wait until the cel animation sets it, on its last cel (DA70DA) | 499 | H |
| 48 | wait_actor_move | actor | wait until the walk reaches its FF (`$7E:B801` bit 6); never returns for an FE list or a walk a wall stops | 2258 | H ✓ |
| 4C | actor_sprite_offset | actor, dx, dy | sprite offset: signed px added to its screen x (`$7E:B812`) and y (`$7E:B811`) when drawn (DA6FFC) | 264 | H ✓ |
| 4D | actor_set_facing | actor, direction | facing 0-3 (`$0707` bits 3-4) | 116 | H |
| 53 | save_actor_position | actor, slot | save its map position to `$04A0 + slot * 4` (slot < 0x18) | 196 | H |
| 54 | restore_actor_position | actor, slot | put it back there, shown | 204 | H |
| 55 | actor_walk_box | actor, x1, y1, x2, y2 | walk box: tiles [x1, x2) x [y1, y2) (`$7E:B813`-`$7E:B816`, 0, 0, 80, 80 at load), checked with the map's collision when a tile starts (`$7E:B801` bit 7, DA53D2) for the player (`$7E:B801` bit 3) and FD random walks only, unless `$7E:B800` bit 1. The pad handler (DA2CC9) clears the player's bit 7 every frame no direction is held, so a scripted player walk checks the tile it starts on only: blocked there, the step's tiles pass without moving; frozen (42 0), every tile is checked and the walk waits at the edge, never done | 69 | H ✓ |
| 66 | object_create | slot, frame, x, y, attr, size, f | raw sprite object: `$0700` = 1, `$0701`, `$0704`, `$0702` (px), `$0707`, `$070A`, `$070F` | 0 | M |
| 67 | object_remove | slot | remove it | 0 | M |
| 83 | actor_place_drawn | actor, x, y | as 12, but on screen (DA432A, carry clear) the sprite is drawn into the OAM now (DA6F63) instead of hidden a frame (DA0F58, `$0706` bit 5) | 82 | H ✓ |
| 88 | call_da781c | id | load animation id (C7 table at C7002C) into the `$7E:FA00` slots, which 22 and 89 run | 8 | M |
| 8A | wait_object | slot | wait until the slot's `$7E:FA00` animation is done | 0 | L |
| 8F | actor_set_sprite_frame | actor, frame | `$0701` and `$070D`, stops the auto-animation | 4 | M |

### Map, camera, layers

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 1B | load_map | map | clear the camera state (`$037C`-`$03D3`), load the map | 268 | H |
| 1C | set_camera | x, y | camera at a tile (16 px), redraws | 341 | H |
| 1D | scroll_camera | x, y, frames | scroll the camera to a tile in `frames` frames (straight, from the script's 3rd frame); the script goes on meanwhile | 69 | H ✓ |
| 1E | shake_bg1 | x, y, frames.w | shake BG1: -x / +x, -y / +y every other frame (`$03B6`, `$03B8`) while `$03C2` counts frames down: frames - 1 frames | 124 | H ✓ |
| 1F | shake_bg2 | x, y, frames.w | same for BG2 (`$03BA`, `$03BC`, `$03C4`) | 55 | H |
| 20 | shake_bg3 | x, y, frames.w | same for BG3 (`$03BE`, `$03C0`, `$03C6`) | 0 | H ✓ |
| 24 | map_set_tile_bg1 | x, y, tile.w | BG1 map tile (tile & 0x9FF), redraws it if on screen | 959 | M |
| 25 | map_set_tile_bg2 | x, y, tile.w | BG2 (tile & 0x8FF) | 50 | M |
| 26 | map_set_attribute | x, y, attribute | collision attribute (& 0x17) in `$7E:6801` | 13 | M |
| 4E | set_tile_priority_a | on | `$032C` = 0 / 0x2000; clears the priority bit over `$7E:A800` (nothing in bank DA reads `$032C`) | 4 | L |
| 4F | set_tile_priority_b | on | same with `$032E` | 4 | L |
| 7D | bg2_velocity | dx, dy | BG2 speed (`$0398` / `$039A`, signed, 1/16 px a frame) while `$42` bit 0 lets it move on its own (73, DA2E11) | 76 | H ✓ |
| 7E | bg3_velocity | dx, dy | BG3 speed (`$039C` / `$039E`) while `$42` bit 2 | 12 | H ✓ |
| 7F | camera_limit | x, y | camera limits: its largest x, y (`$0394` / `$0396` = tile * 16, 6 bits), which the player's walk clamps the camera to (DA2FE1) | 74 | H ✓ |
| 84 | call_da748f |  | E8:CD55 (0x400) to `$7E:E000`, builds 0x800 bytes at `$7E:E400`, DMA to VRAM 3040, then 87 | 1 | L |
| 80 | load_bg3_layer | id | BG3 layer from the C7:0008 record id (DA2558): `+0E` (`$7E:D76E`) high nibble its graphics (C7:0020, LZ to `$7E:E000`, VRAM 4800), low nibble its tilemap (C7:0028, to `$7E:6000`); `+0D` bit 7 (`$7E:D76D`) the priority (DA2805); `$3B` bit 6 uploads | 20 | M |
| 87 | clear_bg3_tilemap |  | fill the BG3 tilemap buffer `$7E:6000` with 0x2008 (86 uploads it) | 22 | H |
| 8B | toggle_8b | mode | HDMA channel 6 to BG3HOFS from `$7E:D790`: 0 one band (DA1B17), else several (DA75D8) | 2 | M |
| 93 | set_map_priority | on | priority bit (0x20 of the high byte) over the BG3 tilemap buffer `$7E:6001` | 1 | M |

### Screen, palettes, windows

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 23 | layer_bg1 | main, sub | BG1 on the main / sub screen (`$6F` / `$70` bit 0) | 87 | H |
| 29 | set_screen | on | 0 forced blank, else display | 739 | H |
| 2A | fade_brightness | from, to, speed, mode | brightness fade (`$3E` bit 4); mode (`$09AD`) bit 0 starts it over at its end (DA4B8F), bit 1 another end case (DA4BA3, not followed) | 664 | H |
| 2B | set_brightness | level | brightness, stops a fade | 0 | H |
| 2C | fade_mosaic | from, to, frames, layers / mode | mosaic size fade from → to over `frames`, on the layers of the high nibble (`$3E` bit 5); the low nibble (`$09B6`) not traced | 21 | M ✓ |
| 2D | set_mosaic | size, layers | `$6E` = size (high nibble), layers (low), to MOSAIC every vblank (DA03E6) | 6 | H ✓ |
| 2E | color_math | cgadsub, time, mode, r, r', g, g', b, b' | colour math: `$71` to CGADSUB on every line (HDMA table `$7E:D801`, DA1DA1); the fixed colour (`$0338`-`$033A`, COLDATA every vblank, DA03EC) fades R r→r', G, B over `time` frames while `$3F` bit 3 (DA4C69). Mode bit 0 starts over at the end, bit 1 goes back and forth | 162 | H ✓ |
| 2F | palette_fade_uniform | first, count, time, repeat, from, to | palette fade: R, G and B each offset (signed, added) from `from` to `to` over `time` (0 at once, 8 about 20 frames, 32 about 70); repeat 1 starts over at the end; the script goes on | 515 | H ✓ |
| 30 | palette_fade_rgb | first, count, time, repeat, 6 bytes | same, `from, to` for R, G, then B | 152 | H ✓ |
| 31 | palette_restore | first, count, time | fade the colours from `$7E:C400` back to the map's (`$7E:C800`, DA5D24) over `time` | 7 | H ✓ |
| 32 | palette_fade_grey | first, count, time, mode | fade to grey: each colour to max(R, G, B) - 4 (DA5C75) over `time`; `$09BF` mode: bit 0 starts over, bit 1 back and forth, bit 2 from grey back | 1 | H ✓ |
| 33 | palette_grey | first, count, on | grey at once (as 32, `$09BF` = 0); 0 fades back (`$09BF` = 4) | 26 | H ✓ |
| 49 | palette_set_fade_base | first, count | copy the colours CGRAM gets (`$7E:C400`, uploaded by `$3B` bits 4-5) to `$7E:C600`, the base 2F, 30, 32, 33 fade from (DA4F9B); FF / FE / FD presets | 100 | H ✓ |
| 4A | layer_bg2 | main, sub | BG2 (bit 1) | 89 | H |
| 4B | layer_bg3 | main, sub | BG3 (bit 2) | 124 | H |
| 51 | load_palette | first, count, data | colours from room data (a room offset) | 13 | H |
| 52 | layer_obj | main, sub | OBJ (bit 4) | 83 | H |
| 5B | setup_windows | 12 bytes | window registers: W12SEL, W34SEL, WOBJSEL, 4 positions (`$09E1`), WBGLOG, WOBJLOG, TMW, TSW, CGWSEL | 15 | M |
| 5C | load_window_shapes | id | `jsl C2001C`: window shape set id, frame index to `$7F:E700`, line offsets `$7F:E800`, lines `$7F:F800` (5D, 5E draw them) | 15 | M ✓ |
| 5D | animate_window_1 | first, last, frames, mode, x, y | window 1 takes the 5C shapes first..last, one every `frames` frames, centred on (x, y) (`$09EE` / `$09EF`, DA5DB3 into the HDMA table `$7F:E000`; the lines outside keep the 5B positions) while `$40` bit 1 (DA5EFB). Mode bit 0 loops, bit 1 back and forth, bit 2 mirrors | 18 | H ✓ |
| 5E | animate_window_2 | first, last, frames, mode, x, y | same for window 2 (`$40` bit 2) | 2 | M |
| 72 | bg2_sway | first, middle, last, a.w, b.w, period | BG2 sway (task 11, DA33CA): each BG2 line first..last scrolls at its own speed (1/16 px, sums in `$7F:E300`), linear from s at first and last to t at middle; (s, t) swing between (a, b) and 0, a quarter every `period` frames (DA0877). HDMA channel 1 to BG2HOFS from `$7F:E000` (DA1DF6), `$6C` bit 1 | 12 | M ✓ |
| 74 | window_1 | off | 0 resumes the window 1 animation (`$40` bit 1); else stops it and puts back the plain 5B window on every line (DA1DB6) | 1 | H ✓ |
| 75 | window_2 | off | same for window 2 (`$40` bit 2, DA1DD6) | 0 | M |
| 76 | windows_off |  | both animations off, `$6C` bit 1 off, windows empty, TMW = TSW = 0, CGWSEL = 2 | 9 | H |
| 77 | move_window_1 | x, y, x', y', frames | move window 1's centre (`$09EE` / `$09EF`) from (x, y) to (x', y') over `frames` frames (`$41` bit 0, DA607F, DA0877 interpolates) | 9 | H ✓ |
| 78 | move_window_2 | x, y, x', y', frames | same for window 2 (`$0A01`-`$0A06`, `$41` bit 1) | 4 | M |
| 79 | bg2_sway_off |  | stop task 11, `$6C` bit 1 off | 5 | H |
| 86 | upload_bg3_tilemap |  | `$3B` bit 6 (upload `$7E:6000` to the BG3 tilemap, VRAM 4C00), one tick | 36 | H |

### Text windows

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 08 | yes_no | text, yes, no | prompt, cursor on 2 lines; A jumps to the line's address, B falls through | 194 | H |
| 09 | multiple_choice | text, a, b, c | same with 3 lines (the `$0964` cursor 0-2); B falls through | 47 | H |
| 34 | set_window_position | row, height | window `$0330` / `$0332`; height in tile rows, two a line (utils.dump_rooms.WindowHeights) | 538 | M |
| 35 | open_window | style | open the window: style not 0 draws its frame (tiles 00-03, flipped at the corners) in the `$7E:4000` tilemap, `$0332` rows high; 0 opens it frameless (`$3F` bit 1). `$3E` bit 1 while open | 2993 | H |
| 36 | close_window |  | close it | 3292 | H |
| 37 | display_text | text | print text in the window (display_dialog_string, DA3AFE, see Text) | 3160 | H ✓ |
| 38 | clear_window_text |  | clear the window's text, when one is open | 561 | M |
| 7B | display_credit | text | credits text (`$41` bit 2 while it prints) | 18 | M |
| 85 | draw_credit_line | x, y, text | credits line at x, y in the A = 1 alphabet (room 248) | 82 | M |

### Sound

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 6A | sound_reset |  | `jsl C30008`: hand the SPC back to its IPL and reload the sound driver (C30056) | 0 | M |
| 6B | play_music | a, b | driver command 04 (music) | 144 | M |
| 6C | music_volume | rate, volume | driver command 13: music volume (7F full); rate 0 at once (SPC 1B, C303D0), else a step every `rate` ticks (SPC 13). 0, 0 zeroes the music voices | 220 | H ✓ |
| 6D | play_sound | id | driver command 00, `$1D02` = 0x80 (sound effect) | 1050 | M |
| 6E | music_volume_b | rate, volume | same code as 6C | 3 | H |
| 6F | sfx_volume | rate, volume | driver command 12: sound effect volume (voices 6-7), SPC 1A / 12 | 201 | H ✓ |
| 92 | music_tempo | rate, offset | driver command 11 (SPC 19 / 11): `$5E` = offset, timer 0 period = the song's (`$5D`) + offset, bigger is slower | 3 | H ✓ |

### Field engine, triggers, system

| op | name | operands | what | uses | |
|---|---|---|---|---|---|
| 22 | animate_to_wram | on | `$3F` bit 5: runs the `$7E:FA00` animations (88) that copy to WRAM (DA79AA; `$3B` bit 4 after) | 110 | M |
| 28 | camera_follow | on | camera follow: 0 sets `$3C` bit 5, the player's walk no longer scrolls the camera (DA1FF2); else clears it | 65 | H ✓ |
| 40 | timer_set | frames.w | timer countdown (`$0329`); at 0 the field runs the +8 script | 1 | H ✓ |
| 41 | timer_run | on | timer on / off (`$3C` bit 7; counts while no script runs) | 1 | H ✓ |
| 42 | player_control | on | 0 freezes the player (`$3C` bit 2) | 930 | H |
| 43 | change_room | room | change room once the script ends (`$0326`, `$3D` bit 7) | 169 | H |
| 44 | set_game_state | 4 bytes | `$0300`-`$0303`, `$3E` bit 3: the field loop jumps to C10000 (battle engine) | 0 | M |
| 45 | system_call | kind, arg | system call: `$0327` picks a vector of DA054B (EE3000 + 4 * kind, kind 8 EE2FE0), most open menu n (`$05FC`) with arg (`$05FE`) | 168 | M ✓ |
| 46 | leave_field |  | leave the field engine (`$3D` bit 4: load_room returns, DA0061) | 18 | M |
| 5A | show_mode7_animation | id | `$0300`, `$40` bit 0: the field loop jumps to D58000 | 44 | M |
| 5F | start_effect_5f | id | `$0301`, `$40` bit 3: jumps to C1000F | 2 | M |
| 60 | area_triggers | on | area triggers (+A table) on / off (`$40` bit 5) | 6 | H |
| 61 | walk_turns_actor | on | `$40` bit 6: a walk step also turns the actor to its direction (`$0707` bits 3-4, DA2342) | 103 | M |
| 69 | request_uploads | mask | `$3B |= mask`: vblank uploads (DA238E): bits 0-3 `$7E:4000`-`$7E:5800` to VRAM 5000-5C00 (BG1, BG2 tilemaps), 4 / 5 `$7E:C400` / `$7E:C500` to CGRAM 00-7F / 80-FF, 6 `$7E:6000` to VRAM 4C00 (BG3 tilemap), 7 `$7E:E000` to VRAM 3200 (text) | 0 | H ✓ |
| 71 | pad_during_scripts | on | `$40` bit 7: the pad handler (DA2C9C) runs even while a script does | 0 | H ✓ |
| 73 | layer_scroll_mode | value | `$42`, from the map header (`$7E:D766`) at load (DA287C): BG2 bit 0 moves on its own (7D), else bit 1 half the camera's move (with bit 4 one and a half), else with it (DA2F11); bits 2 / 3 / 5 the same for BG3; bits 4-7 also pick the load-time speeds (DA28A9) | 91 | H ✓ |
| 7A | start_effect_7a | a, b, c, d, id | `$7E:FFF0`-`$7E:FFF3`, then as 5F | 137 | M |
| 7C | allow_skip | on | Start runs the +C script (`$41` bit 3): the skip | 1 | H ✓ |
| 89 | animate_to_vram | on | `$41` bit 5: runs the `$7E:FA00` animations (88) that queue a VRAM DMA (DA79BB, the `$0A11` queue) | 28 | M |
| 8E | camera_ignore_limit | on | `$41` bit 6: the followed camera ignores the 7F limits (DA2FE5) | 4 | H ✓ |

## Coverage

`uv run python -m utils.vm.room_walk` walks each script room from all its entry points (the header table above),
following every jump, call and branch; it counts the header, its tables, the actor records, every reached
instruction and the texts and palette data they point at. It reaches **310 965 of 314 455 bytes (98.9 %)** of the
83 rooms, and every opcode the round-trip disassembler (`utils.disasm`) walks.

The 3 490 bytes left are 500 ranges:

- 348 single bytes: 165 FE right after a text's FD end, 182 FF after a jump, return or random_branch (padding the
  disassembler used to read as code after random_branch, which never falls through).
- 71 longer ranges decode end to end as instructions (1 457 bytes): dead code, mostly 33-byte blocks repeated
  (`unreached 156e-158e (33 bytes), decodes as 8 ops`) that no header entry or jump reaches. Some may run from
  another room's script or a trigger the walk does not know: L.
- the other 81 (1 685 bytes) do not decode: data nothing points to, or texts whose pointer sits in dead code.

Lowest: room 216 (85.3 %), 214 (88.3 %), 100 (93.8 %). Opcodes no room uses: 01 02 07 20 2B 3A-3C 44 63-6A 71 75 8A
90 94 (they are read from their handlers alone; 8A's one use was room 220's end as the old decompressor garbles it).

## Not checked

The ✓ rows are run in game. Still open:

- L rows: 4E / 4F (`$032C` / `$032E`: nothing in bank DA reads them), 84, 88's C7:002C animations behind 22 / 89,
  91 (EF:0080), 8B's bands (not run), 2A's mode bit 1 (DA4BA3) and the low nibble of 2C (`$09B6`).
- 5E, 75, 78 are window 2's copies of 5D, 74, 77 (same code on the `$0A01` / `$40` bit 2 / `$41` bit 1 state): read,
  not run. 72's speed curve is read from DA33CA; the test only sees BG2's lines move apart.
- Sound: what SPC 11 / 12 / 13 do with their first operand besides the rate (the SPC handlers at ARAM `$1649`'s
  table are not disassembled; volumes and `$5E` were measured).
- Text: F4, F5, F9 operands (DA3BDE, DA3C1E, DA3C4E) are skipped right but what they print is not followed.
- Actor record: `$7E:B800` bits 3-7, `$7E:B802` bits 3-7 have no reader found in the walk code.
