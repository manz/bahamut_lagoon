# Battle opcodes

Every handler of the battle script VM (`battle_opcode_runner` C0:6F00, table C0:7C07), by opcode, as
`utils.vm.battle_script.OPS` names them. The kintsuki projects label each handler `bop_<name>`. Operands in order:
b byte, w word, j code address, t text address, i text-table index.

Confidence: **H** code read fully, **M** mechanism clear, meaning partly, **L** guess. **✓** executed in game by
`tests/test_battle_script.py`: at the decoded address and size for the ones scenario 00's opening runs, and with
its effect asserted in RAM for the ones the assembled test scripts run (utils.vm.battle_asm, on the battle map of
scenario 00). Count by opcode: 96 H, 2 H in part and M for the rest (31's action, 33's orders 2, 3, 5-7), no L;
the 14 entries H, all ✓ but the uncalled 06.

Tools: `uv run python -m utils.vm.battle_script ROOM [--fr] [--bytes]` lists a room's script (entries named,
labels, texts decoded; `--fr` reads the French build). `utils.vm.battle_asm` encodes it back: every room of both
builds re-encodes to its own bytes, and `assemble([op("say", "msg"), "loop", op("jump", "loop"), ...], base=...)`
writes scripts with labels. The French build changes no instruction but the text addresses.

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
  saved by compare / arithmetic / tests (Z bit 1, N bit 7, C bit 0, read by the conditional ops), `$1A05` mode bits
  (80 while a script runs, 40 a unit follows the cursor or the view scrolls, 20 during `use_action_at`, 10
  `hide_cursor`; `exit` clears them), `$1A08` + `$1A20` loop stack, `$1A09` + `$1A40` call stack (8 entries each),
  `$1AC0` 256 local flags (cleared by C0:68D0).
- **Direct page**: the battle runs with D = $0100: `$B1` (the current unit), `$3D` (the action), `$F7`, `$93` ...
  are $7E:01B1, $7E:013D, ...
- **Variables**: 0x60 bytes at $7E:3F90 (`load_var` / `store_var`, operand bit 7 = word). Vars 40-5F are the 256
  battle flags (`set_flag`, `jump_if_flag`). Vars 28-2E are the scripted action (6E), 39-3D the spawn parameters
  (3B), 3A-3F the operands of 6C / 6D. Room flags: 128 bytes at $7F:C000 (`set_room_flag`, `jump_if_room_flag`,
  `map_event`).
- **Units**: a unit operand of FF means the unit in reg. Units 00-0B are the player's (00-05 the squads, 06-0B the
  dragons), 0C-1B the enemy's. A unit's records are at + unit * 0x20 (C0:088C): $7E:2B50 + for 00-0B, $7E:3750 +
  for 0C-1B (unit 0C at $7E:38D0), the map record at $1400 + (x, y at +1, +2; bit 7: off the map). The current
  unit is `$B1` (record `$B2`). Record bytes: +0 bit 7 off the map or defeated, bit 2 the enemy leader (C0:60C9,
  C0:E67C); +3-+6 the characters in a player unit; +8 the map sprite (6-byte records at C7:0030); +9 bit 0 the
  unit is down (C0:D11B defeats it); +0x10 an enemy's AI order (C0:1B1E). Map record: +0x0C bit 0 a scripted pose
  holds the sprite, +0x0D its sprite slot, +0x19 the move type (the column of the move-cost table).
- **Map**: a word per tile, 64 tiles a row. $7E:8000: the occupant (20 | unit, + 40 for the enemy side; 80 a tile
  nothing may enter: 192 of scenario 00's) and the range layer (+1: the move range of the unit at the cursor, or the
  area the current action covers at entries 0C / 08 / 0B). $7F:8000: the tile (& 1FF; its terrain in the tables at
  $7E:7E00 and $7E:6E00) and its state bits (+1): 02 the terrain is transformed (a frozen river, burnt grass), 04
  it burns; 10-80 mark the neighbours of the same terrain and state (C0:45C9, C0:98A6). An action changes the tiles it covers (C0:44FF):
  where its element (record +1) is in the terrain's mask for the tile's state, a plain tile gets 02 (terrain E, 06),
  a 02 tile loses it, a burning one loses 04. The move-cost table $7E:6D10 holds 15 bytes per terrain: for states
  0, 04, 02, that mask then the cost per move type (0: impassable; C0:4B05). Scenario 00: ice (40) freezes the
  river (terrain 3), whose frozen row lets the squads cross, and fire (80) melts it.
- **Ending**: FF (`exit`) frees the unit markers and returns from the runner. `load_unit_byte` (91) also returns
  from the runner when its unit is invalid.

## Entries

`$FB` drives the turn (C0:9EC6): 00 starts it, 10 then 11 the player phase, 80 / 82 end it. `battle_script` names
the entries as below. `test_a_turn_runs_the_phase_entries` ends turn 1 of scenario 00: 07 for units 00, 06, 02,
08, the dragon 07 acts between 0C and 08 (then its 07), 03, then 0A for each enemy, the one in reach acting first
(0C, 0B), 04, and 00, 01, 02 on turn 2. Entries 02, 03, 04, 05, 08, 09, 0B, 0C clear var 28 after the script
(C0:6EC4).

| entry | name | when | caller | |
|---|---|---|---|---|
| 00 | turn_start | turn start (`$FB` 00), before C0:5ED4 and A241; skipped while `$1ABF` = 2 | C0:9E48 | H ✓ |
| 01 | turn_start_2 | turn start, after C0:A241; `$FB` = 10 | C0:9E55 | H ✓ |
| 02 | player_phase | the player phase starts (after the battle-over check), `$FB` = 11 | C0:9E90 | H ✓ |
| 03 | player_phase_end | the player phase is over, the dragons' moves included (`$FB` 80) | C0:9F05 | H ✓ |
| 04 | turn_end | end of the turn, before the turn number ($7E:3BD6) steps (`$FB` 82) | C0:9F15 | H ✓ |
| 05 | victory | C0:E617 reports a won battle: before the all-units experience window (C0:8849) | C0:9F51 | H ✓ |
| 06 | unused_06 | never: no code loads 6 for C0:6ED8 (rooms 4 and 12 still have code there) | none | H |
| 07 | player_moved | a player-side unit, dragon or squad, ended its move | C0:9663 | H ✓ |
| 08 | player_acted | after a player-side action (C0:0B57: C0:CBA8, 44FF, 966D, 0C, 4235, 4047, 08) | C0:0B69, C0:3FA1 | H ✓ |
| 09 | unit_defeated | a unit was defeated, either side, `$1A0E` = it: after an action C0:D11B takes every unit whose record +9 has bit 0 (or the leader with all its characters down) off the map (record bit 7), C0:D18C, and runs it | C0:D209 | H ✓ |
| 0A | enemy_moved | an enemy unit ended its move, whether it moved or not, after its action | C0:1A9A, C0:6182 | H ✓ |
| 0B | enemy_acted | after an enemy action | C0:1DD3, C0:28AD | H ✓ |
| 0C | before_action | before an action, either side; var 32 = 0 first | C0:0B60, C0:2896, C0:3F95 | H ✓ |
| 0D | after_victory | after the experience window, the last script before the battle ends | C0:9F57 | H ✓ |

Stubs 07-0D set `$1A0E` = `$B1` (00-05 leave it); 0C, 08 and 0B also `$1A0C` = `$3D` (the action) and `$1A12` /
`$1A13` = bytes +1, +2 of the action's record (C0:08B7 / EF:4123). The battle-over check C0:E617 sets bit 0 or 1 for a win, 80 / C0
for a loss (C0:9F7C), and the debug build wins on pad 2 B. Entry 05 shares room 4's turn-end code; in most rooms 0D
has closing lines or a `sound_command 13 ..`.

`utils/battle_walk.py` walks every room from its 14 entries: 11085 of 11091 code bytes reached, the rest are dead
`exit` bytes after an `exit` / `return` and one skipped byte in room 15.

## Flow

| op | name | operands | what | |
|---|---|---|---|---|
| 00 | jump | j | | H |
| 01 / 05 | jump_if_equal / jump_if_not_equal | j | on Z | H ✓ |
| 02 / 03 | jump_if_negative / jump_if_positive | j | on N | H |
| 0C / 0D | jump_if_carry / jump_if_no_carry | j | on C: after `compare`, reg >= / < b | H |
| 06 | jump_if_none | j | reg low byte == FF | H |
| 0A / 0B | call / return | j | 8-deep stack; return with an empty stack does nothing | H |
| 54 / 55 | call_if_equal / call_if_not_equal | j | the operand is read either way | H |
| 56 / 57 | return_if_equal / return_if_not_equal | | | H |
| 08 / 09 | loop_start / loop_end | count | count 0 takes reg; loop_end jumps back after loop_start until the count runs out | H |
| 07 | wait | frames | | H |
| 04 | nop | | also every opcode not listed (2D-2F, 32, 34, 3C-3F, 46-4F, 58-5F, 6F-8F, 93-EF, FA-FE) | H |
| 30 | skip_2 | b, b | skips its operands | H |
| FF | exit | | frees the unit markers (F7), clears `$1A05`, ends the script | H ✓ |

## Register, variables, flags

| op | name | operands | what | |
|---|---|---|---|---|
| 10 | compare | b | reg low vs b | H ✓ |
| 11 | test_bits | b | reg low & b, flags only | H |
| 12 / 13 | increment / decrement | | reg low, flags | H |
| 14 / 15 | add / subtract | b | reg low, flags | H |
| 16 / 17 | load / load_word | b / w | | H ✓ (16) |
| 1F | swap_bytes | | reg low <-> high | H |
| 62 / 63 | load_var / store_var | var | $7E:3F90 + var & 7F, a word with bit 7 | H ✓ |
| 60 / 61 | set_flag / clear_flag | flag | bit of $7E:3FD0 | H |
| 52 / 53 | jump_if_flag / jump_unless_flag | flag, j | | H ✓ (52) |
| 0E / 0F | jump_if_local_flag / jump_unless_local_flag | flag, j | bit of $1AC0 (area triggers) | H |
| F4 | set_room_flag | b | $7F:C000 + (b & 7F) = FF, or 00 with bit 7 | H ✓ |
| 50 / 51 | jump_if_room_flag / jump_unless_room_flag | flag, j | room flag nonzero / zero | H |
| 18 | load_turn | | reg = $7E:3BD6, the turn number (1 on the first, 2 after the first end of turn) | H ✓ |
| 1E | load_scenario | | reg low = $7E:3BD8, the scenario: it indexes the per-scenario table EF:AE4D (C0:8849), a lost battle restores it from $7E:3BE4 (C0:9F98); 0 on scenario 00 | H ✓ |
| 64 | load_action | | reg low = `$1A0C`: the action (`$3D`) at entries 0C / 08 / 0B, or `use_action_at`'s; Ice Breath Lv1 is 8C | H ✓ |
| 65 | load_action_element | | reg low = `$1A12`, the action's element (record +1, EF:4121 + C0:08F5; one bit: 80 fire, 40 ice, 08 thunder, 20 poison, 10 earth, 04 holy, 02 dark, 01 healing), reg high = `$1A13` (record +2, flags: 40 most spells, E0 healing, 01 drain). Ice Breath Lv1 (8C) 40 40, Electron (8D) 08 40; rooms 6, 13, 20 test thunder and fire. The element also drives the terrain changes (C0:44FF) | H ✓ |
| F2 | load_sound_byte | b | reg low = $7E:1D00 + b: the bytes `sound_command` sent | H ✓ |

## Units and map

| op | name | operands | what | |
|---|---|---|---|---|
| 19 | load_current_unit | | reg low = `$B1` | H |
| 1D | select_unit | unit | unit (FF: `$1A0E`) on the map → current, camera on it, 32 frames; reg = unit, or FF | H ✓ |
| 1C | select_unit_reg | | select_unit with reg low | H |
| 3A | check_unit | unit | reg = unit if on the map, else FF | H |
| 1A | load_unit_field | offset | reg low = byte `offset` of the current unit's record | H |
| 91 | load_unit_byte | unit, offset | same for `unit`; an invalid unit ends the script | H |
| 90 | load_unit_position | unit | reg = x, y (FF FF without the unit) | H ✓ |
| 1B | find_character_unit | character | reg = the player unit (00-0B) whose characters (record +3-+6) include `character` (FF: reg), else FF; Matelite (03) is in unit 01 | H ✓ |
| 36 | grab_unit | | the current unit follows the cursor (map record +0x18 bit 6, `$1A05` bit 6) | H ✓ |
| 35 | move_cursor | b | bits 6-7 direction (00 / 40 / 80 / C0 → `$9F` 8 up / 4 down / 2 left / 1 right, the pad's bits), bits 0-5 tiles, animated | H ✓ |
| 37 | drop_unit | | the unit leaves its tile (occupant 0) for the cursor's, occupant 20 / 60 + unit | H ✓ |
| 31 | use_action_at | x, y, action | cursor to x, y a tile at a time (`$1A05` bit 5); then `$3D` = `$1A0C` = action and the action runs there like a player's (C0:C1E0, 472D, 469F, CBA8, 44FF, 966D, 93EF, 4235, 4047), entries 0C / 08 left out. Room 0: Matelite's Inspire (35) | H (move) M (action) ✓ |
| 38 | unit_walk_off | dir | grab, then the sprite steps 2 pixels a frame in `dir` (8 up, 4 down, 2 left, 1 right) until off the screen, then remove_unit | H ✓ |
| 39 | remove_unit | | the current unit off the map: its tile's occupant 0, record and map record bit 7 (C0:A021 too for a squad) | H ✓ |
| 3B | spawn_unit | flags | enemy unit 0C + (var 3B & F), if off the map and var 39 < C7:000A: bit 7 sets it up from vars 39-3B (C0:6B6F, EF:0070); bit 6 places it at vars 3C / 3D, else at its record's position; a blocked tile (occupied, off the map, or terrain it cannot cross, C0:4B05) fails unless bit 5 is clear, which tries the 3x3 then 5x5 around it; bit 4 skips the tile check. reg = unit, FF when it fails | H ✓ |
| 33 | set_enemy_order | unit, value | enemy unit (0C-1B, on the map) record +0x10 = value, reg 0; else reg FF. The AI order C0:1B1E dispatches on (00-07): 0 act freely; 1 hold until a player unit comes within 8 tiles (C0:212B; a woken unit wakes the order-1 units within 4) or the leader is on order 0 (C0:211A); 2 / 3 act around the leader and fall back to 0 without one (C0:20C0, C0:1FA9); 4 head for the tile at record +0x0D / +0x0E, hold when that is within 2 of the map edge (C0:1F5C); 5-7 not read. Room 31 sets 0 on turn 10 (the units attack), room 30 sets 0 and 3 | H (0, 1, 4) M (2, 3, 5-7) ✓ |
| 42 | focus_unit | | scrolls the camera to the current unit (`$1A` = `$B1`, C0:A39E) and waits until it stops (`$9B` = 0) | H ✓ |
| 43 | scroll_view | dir, steps | dir 8 / 4 / 2 / 1 as `$9F` (the pad's bits), steps & 3F, `$1A05` bit 6 meanwhile | H ✓ |
| 44 / 45 | shake_screen / stop_shake | b / | `$1A1E` = b (0), 4 frames. C0:5DFE then offsets the screen by a random amount within b & 1F (centred) in x with bit 7, in y with bit 6 | H ✓ |
| 66 | test_area_in_range | x, y, w, h | Z = no tile of the rectangle in the range layer ($7E:8000 + 1): at entries 0C / 08 / 0B, whether the action hits it | H ✓ |
| 67 | test_unit_in_range | unit | flags from the range layer under the unit (Z: not in it, or no such unit) | H |
| 68 | load_tile_unit | x, y | reg = the occupant byte at x, y (FF FF: reg; out of the map: FF); Z = no unit there | H ✓ |
| 69 | test_unit_can_enter | x, y, unit | whether `unit` (FF: reg) may stand at x, y: reg 0 if the tile is free and its move type (map record +0x19) can cross the terrain (C0:4B05: the cost for the tile's state is not 0), or the unit is already there; 1 a unit of its side is there, the terrain passable; 80 a unit of the other side, or terrain it cannot cross; FF no such unit. Nothing is counted | H ✓ |
| 6A | test_area_terrain | x, y, w, h | over the tiles of the rectangle with no 80 occupant: reg 0 when none is transformed or burning (state bits 02 / 04, $7F:8000 + 1), 1 some, 80 all, FF out of the map; Z with 0. Room 0 tests whether the river is frozen across | H ✓ |
| 6B | load_terrain | x, y | reg low = terrain ($7E:7E00[tile] & F) + 40 when transformed (state 02), 80 when burning (04); reg high = $7E:6E00[tile] & F; x FF: reg; x bit 6: the tile under unit y (FF: the current unit); FF out of the map. Scenario 00's river is 3, frozen 43: room 0 warns the unit standing on it | H ✓ |
| 6C | test_unit_can_enter_vars | | 69 with x, y, unit from vars 3C, 3D, 3A. Room 0 steps an enemy one tile up when it may | H ✓ |
| 6D | test_area_terrain_vars | | 6A with x, y, w, h from vars 3C-3F | H ✓ |
| 92 | find_enemy_leader | | reg = the enemy leader, the first enemy unit whose record has bit 2 (C0:60C9), FF if none or if it is off the map. Defeating it wins the battle (C0:E617 bit 02); room 29 picks its victory line ("defeat the leader" / "all enemies") with it | H ✓ |
| 6E | queue_scripted_action | 7 bytes | to vars 28-2E. At the next turn start (C0:5ED4 → C0:5F36), unless the battle is over, the enemy leader performs it at vars 3C / 3D: var 28 the action (`$3D`), 29 / 2A an animation (`$81` / `$89`, C0:CBDE, none when 29 is 0), 2B `$3F`, 2C the screen offsets (bits 80-10 → `$8C`-`$8F`), 2D the area (bits 7 / 6 / 5 three fixed shapes, else a radius of & F), 2E the name shown (C7:0038, 8 letters); then the damage and defeats (C0:42C8, C0:D11B) and var 28 = 0. Without a leader nothing plays. Rooms 7 (its cannons), 9, 10, 13-15, 20, 22, 23, 30 | H ✓ (vars) |
| F0 | map_event | n | redraw (C0:4047), then map event n ($7F:C282 + 4n: room flag | bit 7, ...): applied only while the room flag's bit 7 matches the event's (flag 7F: always), which flips the flag; its tiles then change | H ✓ |
| F5 | map_event_f5 | n | the same without the redraw first; `$1A62` = FF, which C0:97EC / 9803 test while applying | H ✓ |
| F6 | refresh_map | | C0:4047 alone: redraws the map from $7F:8000 (C0:53B8, BE1A), the redraw `map_event` starts with | H |
| F7 | set_unit_pose | unit, kind | plays animation kind & F (word table C6:B400) on the unit's map sprite in a slot of 8 (`$1A68` = 80 + unit, map record +0x0D its sprite slot), waiting until it ends (C0:859B). Commands: 00 end (pose off), 01 n frame n (map record +0x0C bit 0: the pose holds), 02 b flip bits, 03 / 04 / 05 move x / y / both, 06 n wait n frames, 07 a frame, 08 x y place, 09 end, pose held. Kinds 1-8 hold a frame or a short sequence (8 a hop), 0 and 9-15 end it; exit drops every held pose. Reg FF when the unit is off the map or no slot is free | H ✓ |
| F8 / F9 | set_unit_sprite / restore_unit_sprite | unit, value / unit | record +8, the map sprite (C7:0030 records: graphics, palette), saved to +0x1C and set / put back, the unit redrawn (C0:6725, C0:BCD0) | H ✓ |
| F3 | give_item | item, count | adds to the inventory (item, count pairs at $7E:3AD0, capped at 99), shows the item line (C0:7720) | H ✓ |
| F1 | sound_command | 4 bytes | to $7E:1D00, jsl C3:0000: the sound driver runs command byte 0 (table C3:0883). The scripts send 00 id 80 00 a sound effect, 01 id 01 xx a looping one (voices 6-7), 12 n fade that out over n, 13 n fade the music out (00: at once; most rooms' entry 0D), 05 song 03 F0 change the music (fades to song 1C in room 0). Checked on the DSP voices in game | H (00, 01, 05, 12, 13) ✓ |
| 40 / 41 | hide_cursor / show_cursor | | `$1A05` bit 4: C0:EB65, its only reader, skips drawing the map cursor | H ✓ |

## Text

Texts are copied to $7E:C000 (0xE0 bytes, `copy_battle_text`) and shown by `display_battle_text` +
`battle_string_manip`. Control codes: F4-F8, FA, FC take a byte, F9 a word; FE a new line, FD waits, FF ends. The
vanilla texts are font pages F0-F3 and a byte; the French ones a byte.

| op | name | operands | what | |
|---|---|---|---|---|
| 20 | open_window | | message window at the bottom (`$F7` = A0), at the top (01) when `$93` >= 0B | H ✓ |
| 21 / 25 | open_window_top / open_window_bottom | | `$F7` = 01 / A0 | H ✓ |
| 22 | close_window | | closes the message window (C0:E46D), `$A9` = 0, `$F7` back to A0, the window HDMA table back to 055F | H ✓ |
| 24 | clear_window | | clears the text buffer (C0:A3DF) and DMAs 0xB40 bytes of 7E:D000 to VRAM 4180 | H ✓ |
| 26 | say | t | copy + show | H ✓ |
| 23 | say_index | i | text i of the text table, copy + show | H |
| 29 / 28 | load_text / load_text_index | t / i | copy only | H |
| 2A | set_text_arg | n, b | the argument of the n-th (from 1) control code (F4-F8, FA, FC; F9 takes a word) of the loaded text = b; n bit 7: reg instead (b still read). The scan counts every byte, arguments too | H |
| 2B | set_text_arg_word | n, w | the same with a word | H |
| 2C | say_loaded | | show the loaded text | H |
| 27 | ask_yes_no | t | copies 0x20 bytes at t to $0720 (the prompt), draws them with a yes / no choice and waits (C0:37F7, cursor `$B5` 3 yes / 4 no); its flags land in `$1A04`: Z yes, not Z no, N cancelled with B | H ✓ |

## Not verified

Unused by the vanilla scripts (decoded from the handlers only): 0C, 0D, 11, 14, 15, 17, 1A, 1E, 21, 23, 27-2C, 30,
55-57, 67, 69, 6D, 91, F2, F7-F9. 1E, 21, 27, 69, 6D, F2, F7, F8, F9 ran in the assembled tests. Still open: AI
orders 2, 3, 5-7 (33) past their dispatch, the flags in action record +2 (65), what `use_action_at` (31) leaves out
of a player's action besides entries 0C / 08. The scripted action (6E) plays only with a leader on the map: no test
has one alive (a forced leader bit makes the battle won at once, its characters reading as down), so its turn-start
play is read from the code.
