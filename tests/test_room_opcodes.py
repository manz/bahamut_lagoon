"""
Room script opcodes checked in game (docs/vm/dialog_opcodes.md, the ✓ marks): on the field after New Game
(new-game-field, room 0 idle), a script written past the room's end in its buffer runs as the header's +C script,
which the field loop starts when `$41` bit 4 is set (DA043C). Room bits (`$0312`, opcode 62) say which way it went.
"""

from collections.abc import Callable, Sequence

from tests.conftest import Console
from utils.vm.room_asm import Op, assemble, op

Script = Sequence[str | Op | bytes]

ROOM_POINTER = 0x7E0067  # [$67]: the room's start, its buffer in bank 7F
ROOM_BITS = 0x7E0312
ROOM_EVENTS = 0x7E0041  # bit 3: Start runs the +C script (opcode 7C), bit 4: run it now
SCRIPT_AT = 0x1400  # past room 0's 0x12CB bytes
TIMER_SCRIPT_AT = 0x1440
SKIP_SCRIPT_AT = 0x1480
ROOM_BYTES = 0x7E3BD0  # set_var / add_var table 4: a byte array indexed by the field operand alone
# Room 0's actors: 0 the player, 6 one free to walk left, right and down. Sprite objects `$0700 + n * 0x10` (y
# `+2`, x `+4`, in px from the camera; displayed frame `+1`, set frame `+0D`), script records `$7E:B800 + n * 0x80`.
PLAYER = 0
WALKER = 6
CAMERA_X = 0x7E037C
CAMERA_Y = 0x7E037E
PLAYER_Y = 0x7E0702
PLAYER_STATE = 0x7EB801  # the player's `$7E:B801`: bit 6 its motion list is done
WALKER_X = 0x7E0764
WALKER_Y = 0x7E0762
WALKER_FRAME = 0x7E0761
WALKER_STATE = 0x7EBB01  # bit 6: its motion list is done
WALKER_OAM = 56  # the OAM entries that draw it, 56-58
UP, DOWN, LEFT, RIGHT = 0x00, 0x10, 0x20, 0x30  # a step's direction (high nibble); its tile count is the low one
END, LOOP, PAUSE = 0xFF, 0xFE, 0xFC  # motion list codes


class Room:
    def __init__(self, console: Console) -> None:
        console.load("new-game-field")
        self.console = console
        self.emu = console.emu
        self.base = int.from_bytes(bytes(self.emu.read_range(ROOM_POINTER, 3)), "little")

    def byte(self, address: int) -> int:
        return bytes(self.emu.read_range(address, 1))[0]

    def word(self, address: int) -> int:
        return int.from_bytes(bytes(self.emu.read_range(address, 2)), "little")

    def frames_until(self, done: Callable[[], bool], limit: int = 300) -> int | None:
        """Frames run until done(), None past the limit."""
        for frame in range(limit):
            if done():
                return frame
            self.emu.run_frames(1)
        return None

    def walk_done(self) -> bool:
        return bool(self.byte(WALKER_STATE) & 0x40)

    def put(self, at: int, script: Script) -> None:
        self.emu.write_range(self.base + at, assemble(script, at)[0])

    def header(self, offset: int, at: int) -> None:
        self.emu.write_range(self.base + offset, at.to_bytes(2, "little"))

    def run(self, script: Script, frames: int = 30) -> None:
        """Run script once as the +C script."""
        self.put(SCRIPT_AT, script)
        self.header(0x0C, SCRIPT_AT)
        self.emu.write_range(ROOM_EVENTS, bytes([self.byte(ROOM_EVENTS) | 0x10]))
        self.emu.run_frames(frames)


def test_add_var_clamped_clamps_to_its_maximum(console: Console) -> None:
    """90: table 4 skips the record byte (77 here); 4 + 5 clamped to 7."""
    room = Room(console)
    room.emu.write_range(ROOM_BYTES + 0x10, b"\x04")
    room.run([op("add_var_clamped", 4, 0x77, 0x10, 5, 0, 7), op("exit")])
    assert room.byte(ROOM_BYTES + 0x10) == 7


def test_add_var_clamped_clamps_to_its_minimum(console: Console) -> None:
    """90: 4 + FE wraps to 2, raised to the minimum 3."""
    room = Room(console)
    room.emu.write_range(ROOM_BYTES + 0x10, b"\x04")
    room.run([op("add_var_clamped", 4, 0, 0x10, 0xFE, 3, 7), op("exit")])
    assert room.byte(ROOM_BYTES + 0x10) == 3


def test_the_timer_runs_the_header_8_script_when_it_runs_out(console: Console) -> None:
    """40 sets the countdown (frames), 41 starts it; at 0 the field runs the +8 script."""
    room = Room(console)
    room.put(TIMER_SCRIPT_AT, [op("set_room_bits", 0x02), op("exit")])
    room.header(0x08, TIMER_SCRIPT_AT)
    room.run([op("timer_set", 60), op("timer_run", 1), op("exit")], frames=20)
    early = room.byte(ROOM_BITS) & 0x02
    room.emu.run_frames(80)
    assert (early, room.byte(ROOM_BITS) & 0x02) == (0, 0x02)


def test_start_runs_the_skip_script_once_allowed(console: Console) -> None:
    """7C 01 lets Start run the +C script."""
    room = Room(console)
    room.run([op("allow_skip", 1), op("exit")])
    room.put(SKIP_SCRIPT_AT, [op("set_room_bits", 0x04), op("exit")])
    room.header(0x0C, SKIP_SCRIPT_AT)
    before = room.byte(ROOM_BITS) & 0x04
    console.tap(console.button.START)
    assert (before, room.byte(ROOM_BITS) & 0x04) == (0, 0x04)


def test_open_menu_hands_its_kind_to_the_system_bank(console: Console) -> None:
    """45 kind 6 goes through the EE3018 vector: menu 7 in `$05FC`, the argument in `$05FE`."""
    room = Room(console)
    room.emu.write_range(0x7E05FC, bytes(4))
    room.run([op("system_call", 6, 3), op("exit")], frames=10)
    assert bytes(room.emu.read_range(0x7E05FC, 4)) == bytes.fromhex("07000300")


def test_wait_actor_move_returns_once_the_list_reaches_ff(console: Console) -> None:
    """13 walks the steps (2 tiles of 16 px right), FF sets `$7E:B801` bit 6, which 48 waits for."""
    room = Room(console)
    room.run(
        [op("actor_move", WALKER, [RIGHT | 2, END]), op("wait_actor_move", WALKER), op("set_room_bits", 1), op("exit")],
        1,
    )
    x = room.word(WALKER_X)
    room.emu.run_frames(40)
    assert (room.byte(ROOM_BITS) & 1, room.word(WALKER_X) - x) == (1, 0x20)


def test_a_motion_list_ending_on_fe_starts_over(console: Console) -> None:
    """FE loops the list: the walker goes right and back forever, never done."""
    room = Room(console)
    room.run([op("actor_move", WALKER, [RIGHT | 1, LEFT | 1, LOOP]), op("exit")], frames=1)
    xs = set()
    for _ in range(200):
        xs.add(room.word(WALKER_X))
        room.emu.run_frames(1)
    assert (room.walk_done(), min(xs) + 0x10) == (False, max(xs))


def test_fc_in_a_motion_list_waits_60_frames(console: Console) -> None:
    room = Room(console)
    room.run([op("actor_move", WALKER, [RIGHT | 1, LEFT | 1]), op("exit")], frames=1)
    plain = room.frames_until(room.walk_done)
    room = Room(console)
    room.run([op("actor_move", WALKER, [RIGHT | 1, PAUSE, LEFT | 1]), op("exit")], frames=1)
    paused = room.frames_until(room.walk_done)
    assert plain is not None and paused == plain + 60


def test_a_step_of_no_tiles_only_turns(console: Console) -> None:
    room = Room(console)
    x = room.word(WALKER_X)
    room.run([op("actor_move", WALKER, [RIGHT]), op("exit")], frames=1)
    assert (room.frames_until(room.walk_done), room.word(WALKER_X)) == (5, x)


def walk_frames(room: Room, script: Script) -> set[int]:
    """The walker's displayed frames while it walks right and back."""
    room.run([*script, op("actor_move", WALKER, [RIGHT | 2, LEFT | 2]), op("exit")], frames=1)
    frames = set()
    for _ in range(40):
        frames.add(room.byte(WALKER_FRAME))
        room.emu.run_frames(1)
    return frames


def test_actor_set_frame_holds_the_frame_while_walking(console: Console) -> None:
    """0E sets `$7E:B801` bit 5: the walk tick (DA2075) leaves the frame alone."""
    room = Room(console)
    assert walk_frames(room, [op("actor_set_frame", WALKER, 9)]) <= {1, 9}


def test_actor_set_animated_gives_the_walk_its_frames_back(console: Console) -> None:
    room = Room(console)
    assert len(walk_frames(room, [op("actor_set_frame", WALKER, 9), op("actor_set_animated", WALKER, 1)])) > 3


def test_actor_set_animated_off_freezes_the_walk_frames(console: Console) -> None:
    room = Room(console)
    assert len(walk_frames(room, [op("actor_set_animated", WALKER, 0)])) == 1


def test_actor_sprite_offset_offsets_the_sprite(console: Console) -> None:
    """4C actor, dx, dy: signed pixels added to the sprite's screen position (DA6FFC), x from `$7E:B812`."""
    room = Room(console)
    room.run([op("actor_set_animated", WALKER, 0), op("exit")], frames=10)
    before = bytes(room.emu.oam_read_range(4 * WALKER_OAM, 4))
    room.run([op("actor_sprite_offset", WALKER, 0x10, 0xF8), op("exit")], frames=10)
    after = bytes(room.emu.oam_read_range(4 * WALKER_OAM, 4))
    assert (after[0] - before[0], before[1] - after[1]) == (0x10, 8)


def actors_held(room: Room, hold: bool) -> list[int]:
    """The walker's x every 10 frames, walking 4 tiles left, held for 60 frames from the 10th when hold."""
    script = [op("actor_move", WALKER, [LEFT | 4]), op("wait_frames", 10)]
    if hold:
        script += [op("actors_hold", [WALKER]), op("wait_frames", 60), op("actors_release", [WALKER])]
    room.run([*script, op("exit")], frames=1)
    xs = []
    for _ in range(15):
        xs.append(room.word(WALKER_X))
        room.emu.run_frames(10)
    return xs


def test_actors_hold_stops_the_walker_on_a_tile_until_released(console: Console) -> None:
    """14 waits for the step to end, then `$7E:B801` bit 1 stops the walk there; 18 lets it go on."""
    room = Room(console)
    xs = actors_held(room, hold=True)
    held = xs[3:7]
    assert (len(set(held)), held[0] % 0x10, xs[-1]) == (1, 0, actors_held(Room(console), hold=False)[-1])


def camera_after_walking_down(room: Room, script: Script, steps: int = 4) -> int:
    """The camera's y once the player walked `steps` tiles down (room 0 has room for 4)."""
    room.run([*script, op("actor_move", PLAYER, [DOWN | steps]), op("wait_actor_move", PLAYER), op("exit")], frames=120)
    return room.word(CAMERA_Y)


def test_the_camera_follows_the_player(console: Console) -> None:
    assert camera_after_walking_down(Room(console), []) == 0x50


def test_camera_follow_off_stops_the_camera_following(console: Console) -> None:
    """28 0 sets `$3C` bit 5: the walk step (DA1FF2) no longer scrolls the camera."""
    assert camera_after_walking_down(Room(console), [op("camera_follow", 0)]) == 0x10


def test_camera_limit_limits_the_camera(console: Console) -> None:
    """7F x, y: the camera's largest x, y (`$0394`, `$0396`, in tiles), which a followed walk clamps to (DA2FE1)."""
    assert camera_after_walking_down(Room(console), [op("camera_limit", 0x10, 3)]) == 0x30


def test_camera_ignore_limit_lets_the_camera_past_its_limit(console: Console) -> None:
    """8E 1 sets `$41` bit 6: no clamp."""
    script = [op("camera_limit", 0x10, 1), op("camera_ignore_limit", 1)]
    assert camera_after_walking_down(Room(console), script) == 0x50


def walk_down_by_pad(room: Room, script: Script) -> int:
    """The player's map y (px) after holding Down for 90 frames."""
    room.run([*script, op("exit")], frames=5)
    room.emu.press(0, room.console.button.DOWN)
    room.emu.run_frames(90)
    room.emu.release(0, room.console.button.DOWN)
    room.emu.run_frames(20)
    return room.word(CAMERA_Y) + room.word(PLAYER_Y)


def test_actor_walk_box_keeps_the_player_in_a_box(console: Console) -> None:
    """55 actor, x1, y1, x2, y2: tiles [x1, x2) x [y1, y2) (`$7E:B813`-`$7E:B816`); the player starts on row 9."""
    rows = [walk_down_by_pad(Room(console), [op("actor_walk_box", PLAYER, 0, 0, 0x80, y2)]) >> 4 for y2 in (10, 12)]
    assert rows == [9, 11]


def test_actor_set_behavior_bit_1_walks_through_walls(console: Console) -> None:
    """17: `$7E:B800` bit 1 skips the map collision and the box (DA1F5D); room 0 stops the player on row 13."""
    plain = walk_down_by_pad(Room(console), [])
    through = walk_down_by_pad(Room(console), [op("actor_set_behavior", PLAYER, 2)])
    assert (plain >> 4, through > plain) == (13, True)


def colour(room: Room, index: int) -> tuple[int, int, int]:
    value = int.from_bytes(bytes(room.emu.cgram_read_range(2 * index, 2)), "little")
    return value & 0x1F, value >> 5 & 0x1F, value >> 10 & 0x1F


def test_palette_fade_uniform_fades_by_an_offset(console: Console) -> None:
    """2F first, count, time, repeat, from, to: R, G and B each offset from `from` to `to` (signed); colour 21 is
    pure red, faded to black by -31 (E1)."""
    room = Room(console)
    start = colour(room, 0x21)
    room.run([op("palette_fade_uniform", 0xFE, 0, 8, 0, 0, 0xE1), op("exit")], frames=60)
    assert (start, colour(room, 0x21)) == ((31, 0, 0), (0, 0, 0))


def test_palette_fade_rgb_fades_each_component(console: Console) -> None:
    """30 first, count, time, repeat, then from, to for R, G and B: only blue gains 12 here."""
    room = Room(console)
    red, green, blue = colour(room, 0x12)
    room.run([op("palette_fade_rgb", 0xFE, 0, 16, 0, 0, 0, 0, 0, 0, 12), op("exit")], frames=80)
    assert colour(room, 0x12) == (red, green, blue + 12)


def test_scroll_camera_takes_its_frames_and_does_not_wait(console: Console) -> None:
    """1D x, y, frames: the camera (`$037C`, `$037E`) reaches tile (2, 6) 16 frames after it starts moving."""
    room = Room(console)
    room.run([op("scroll_camera", 2, 6, 16), op("set_room_bits", 1), op("exit")], frames=0)
    arrived = room.frames_until(lambda: (room.word(0x7E037C), room.word(CAMERA_Y)) == (0x20, 0x60), limit=40)
    assert (arrived, room.byte(ROOM_BITS) & 1) == (18, 1)


def test_fb_in_a_motion_list_waits_30_frames(console: Console) -> None:
    room = Room(console)
    room.run([op("actor_move", WALKER, [RIGHT | 1, LEFT | 1]), op("exit")], frames=1)
    plain = room.frames_until(room.walk_done)
    room = Room(console)
    room.run([op("actor_move", WALKER, [RIGHT | 1, 0xFB, LEFT | 1]), op("exit")], frames=1)
    paused = room.frames_until(room.walk_done)
    assert plain is not None and paused == plain + 30


def test_diagonal_steps_move_a_tile_on_both_axes(console: Console) -> None:
    """Directions 4-7 (DA20D7): up-left, down-right, down-left, up-right."""
    moves = []
    for direction in (0x40, 0x50, 0x60, 0x70):
        room = Room(console)
        x, y = room.word(WALKER_X), room.word(WALKER_Y)
        room.run([op("actor_move", WALKER, [direction | 1]), op("wait_actor_move", WALKER), op("exit")], frames=60)
        moves.append((room.word(WALKER_X) - x, room.word(WALKER_Y) - y))
    assert moves == [(-16, -16), (16, 16), (-16, 16), (16, -16)]


def test_the_walk_box_does_not_hold_a_scripted_actor(console: Console) -> None:
    """The box (and the map) are checked for the player (`$7E:B801` bit 3) and FD random walks only (DA1F34)."""
    room = Room(console)
    x = room.word(WALKER_X)
    room.run([op("actor_walk_box", WALKER, 0, 0, 1, 1), op("actor_move", WALKER, [RIGHT | 2]), op("exit")], frames=80)
    assert (room.word(WALKER_X) - x, room.walk_done()) == (0x20, True)


def player_rows_walked(room: Room, script: Script, y2: int) -> tuple[int, bool]:
    """Rows the player walks of a scripted 4-tile walk down from row 9, inside a box ending on row y2; and whether
    its list ended."""
    y = room.word(CAMERA_Y) + room.word(PLAYER_Y)
    walk = [op("actor_walk_box", PLAYER, 0, 0, 0x80, y2), op("actor_move", PLAYER, [DOWN | 4])]
    room.run([*script, *walk, op("exit")], frames=150)
    return (room.word(CAMERA_Y) + room.word(PLAYER_Y) - y) >> 4, bool(room.byte(PLAYER_STATE) & 0x40)


def test_a_scripted_player_walk_checks_the_box_on_its_first_tile_only(console: Console) -> None:
    """The pad handler (DA2CC9) clears the player's `$7E:B801` bit 7 (check the next tile) every frame no direction
    is held: only the tile the walk starts on is checked. Blocked there, the step's tiles pass without moving."""
    walked = [player_rows_walked(Room(console), [], y2) for y2 in (10, 11)]
    assert walked == [(0, True), (4, True)]


def test_a_frozen_player_walk_stops_at_the_box_edge(console: Console) -> None:
    """42 0 skips the pad handler (DA2C9C): every tile is checked and the walk waits at the edge, never done."""
    assert player_rows_walked(Room(console), [op("player_control", 0)], 12) == (2, False)


def walker_oam_entry(room: Room) -> int:
    """The first OAM entry drawing the walker (its sprite at x A0, y 67)."""
    oam = bytes(room.emu.oam_read_range(0, 512))
    return next(i for i in range(128) if oam[4 * i : 4 * i + 2] == b"\xa0\x67")


def test_actor_draw_order_puts_the_sprite_behind_or_in_front(console: Console) -> None:
    """21: 1 sets `$0707` bit 6, the sprite goes last in OAM (behind every sprite), 3 bit 5, first (in front)."""
    entries = []
    for mode in (0, 1, 3):
        room = Room(console)
        room.run([op("actor_set_animated", WALKER, 0), op("actor_draw_order", WALKER, mode), op("exit")], frames=10)
        entries.append(walker_oam_entry(room))
    assert entries == [48, 116, 0]


def walker_sprite(room: Room) -> bytes:
    """x, y of the walker's first OAM entry (tile 60, attributes 2A), wherever the depth sort puts it."""
    oam = bytes(room.emu.oam_read_range(0, 512))
    return next(oam[4 * i : 4 * i + 2] for i in range(128) if oam[4 * i + 2 : 4 * i + 4] == b"\x60\x2a")


def oam_x_after_placing(console: Console, name: str) -> list[bytes]:
    """The walker's sprite position the 3 frames after placing it 2 tiles left of where it stands."""
    room = Room(console)
    room.run([op("actor_set_animated", WALKER, 0), op("exit")], frames=10)
    tx, ty = (room.word(WALKER_X) >> 4) - 2, room.word(WALKER_Y) >> 4
    room.run([op(name, WALKER, tx, ty), op("wait_frames", 30), op("exit")], frames=0)
    xs = []
    for _ in range(3):
        room.emu.run_frames(1)
        xs.append(walker_sprite(room))
    return xs


def test_actor_place_drawn_draws_the_sprite_at_once(console: Console) -> None:
    """83 draws the placed sprite now (DA6F63); 12 sets `$0706` bit 5 and hides it (y E0) a frame first."""
    assert (oam_x_after_placing(console, "actor_place"), oam_x_after_placing(console, "actor_place_drawn")) == (
        [b"\xa0\x67", b"\xa0\xe0", b"\x10\x57"],
        [b"\xa0\x67", b"\x10\x57", b"\x10\x57"],
    )


def scroll_after_camera_move(console: Console, mode: int) -> tuple[int, int]:
    """How far BG2 and BG3 scroll while the camera moves 8 tiles right, under layer_scroll_mode `mode`."""
    room = Room(console)
    room.run([op("bg2_velocity", 0, 0), op("layer_scroll_mode", mode), op("set_camera", 0, 0), op("exit")], frames=10)
    before = room.emu.get_ppu_state()
    bg2, bg3 = before.bg_hofs(2), before.bg_hofs(3)
    room.run([op("set_camera", 8, 0), op("exit")], frames=10)
    after = room.emu.get_ppu_state()
    return after.bg_hofs(2) - bg2, after.bg_hofs(3) - bg3


def test_layer_scroll_mode_sets_how_bg2_and_bg3_follow_the_camera(console: Console) -> None:
    """73 (`$42`): bits 0 / 2 BG2 / BG3 move on their own (7D / 7E), bits 1 / 3 half the camera's move, with 4 / 5
    one and a half (DA2F11); else with the camera, 0x80 px here."""
    modes = (0x00, 0x01, 0x02, 0x12, 0x04, 0x08, 0x28)
    assert [scroll_after_camera_move(console, mode) for mode in modes] == [
        (128, 128),
        (0, 128),
        (64, 128),
        (192, 128),
        (128, 0),
        (128, 64),
        (128, 192),
    ]


def hofs_offsets(room: Room, script: Script, layer: int, frames: int = 20) -> list[int]:
    """The layer's horizontal scroll each frame, from the frame the script starts on, less the first one."""
    room.run([op("bg2_velocity", 0, 0), *script, op("exit")], frames=1)
    first = room.emu.get_ppu_state().bg_hofs(layer)
    offsets = []
    for _ in range(frames):
        offsets.append((room.emu.get_ppu_state().bg_hofs(layer) - first + 0x200) % 0x400 - 0x200)
        room.emu.run_frames(1)
    return offsets


def test_shake_bg1_shakes_the_layer_for_its_frames(console: Console) -> None:
    """1E x, y, frames: BG1 swings -x / +x every frame (`$03B6`) until `$03C2`, set to frames, counts down to 0:
    frames - 1 frames shaken."""
    offsets = hofs_offsets(Room(console), [op("shake_bg1", 3, 1, 8)], 1)
    assert offsets[:11] == [0, 0, -3, 3, -3, 3, -3, 3, -3, 0, 0]


def test_shake_bg3_shakes_bg3(console: Console) -> None:
    offsets = hofs_offsets(Room(console), [op("shake_bg3", 2, 0, 4)], 3, frames=8)
    assert offsets == [0, 0, -2, 2, -2, 0, 0, 0]


def test_bg3_velocity_scrolls_bg3_in_sixteenths_of_a_pixel(console: Console) -> None:
    """7E dx, dy (signed, 1/16 px a frame) while `$42` bit 2 (73) lets BG3 move on its own."""
    offsets = hofs_offsets(Room(console), [op("layer_scroll_mode", 0x05), op("bg3_velocity", 0x20, 0)], 3, frames=9)
    assert offsets[-1] - offsets[1] == 14


def test_color_math_fades_the_fixed_colour(console: Console) -> None:
    """2E cgadsub, time, mode, then R, G, B (from, to): `$71` goes to CGADSUB through the HDMA table at `$7E:D800`,
    the fixed colour (`$0338`-`$033A`) to COLDATA every vblank (DA03EC). Mode 1 starts the fade over."""
    room = Room(console)
    written: dict[int, set[int]] = {0x2131: set(), 0x2132: set()}
    room.emu.add_write_callback(0x2131, 0x2132, lambda address, value: written[address].add(value))
    room.run([op("color_math", 0x21, 8, 1, 0, 31, 0, 0, 10, 0), op("exit")], frames=1)
    reds = []
    for _ in range(12):
        reds.append(room.byte(0x7E0338))
        room.emu.run_frames(1)
    assert (reds, 0x21 in written[0x2131], 0x20 | 31 in written[0x2132]) == (
        [0, 3, 7, 11, 15, 19, 23, 27, 31, 31, 3, 7],
        True,
        True,
    )


def test_palette_set_fade_base_makes_the_current_colours_the_fades_base(console: Console) -> None:
    """49 copies `$7E:C400` (the colours CGRAM gets) to `$7E:C600`, which 2F, 30, 32 and 33 fade from (DA4F9B): a
    zero-offset fade after it keeps red colour 21 black."""
    dark = op("palette_fade_uniform", 0xFE, 0, 0, 0, 0xE1, 0xE1)
    zero = op("palette_fade_uniform", 0xFE, 0, 0, 0, 0, 0)
    room = Room(console)
    room.run([dark, op("wait_frames", 5), zero, op("exit")], frames=40)
    kept = colour(room, 0x21)
    room = Room(console)
    room.run([dark, op("wait_frames", 5), op("palette_set_fade_base", 0x21, 1), zero, op("exit")], frames=40)
    assert (kept, colour(room, 0x21)) == ((31, 0, 0), (0, 0, 0))


def test_palette_restore_fades_back_to_the_map_palette(console: Console) -> None:
    """31 first, count, time: from the current colours to the map's (`$7E:C800`, DA5D24)."""
    room = Room(console)
    darkened = [op("palette_fade_uniform", 0xFE, 0, 0, 0, 0xE1, 0xE1), op("wait_frames", 5)]
    room.run([*darkened, op("palette_restore", 0xFE, 0, 1), op("exit")], frames=40)
    assert colour(room, 0x21) == (31, 0, 0)


def test_palette_grey_and_back(console: Console) -> None:
    """33 on: each colour to grey, max(R, G, B) - 4 (DA5C75); 33 0 fades back from grey (`$09BF` bit 2)."""
    room = Room(console)
    room.run([op("palette_grey", 0xFE, 0, 1), op("exit")], frames=20)
    grey = colour(room, 0x21), colour(room, 0x12)
    room.run([op("palette_grey", 0xFE, 0, 0), op("exit")], frames=20)
    assert (grey, colour(room, 0x21)) == (((27, 27, 27), (0, 0, 0)), (31, 0, 0))


def test_palette_fade_grey_takes_its_time(console: Console) -> None:
    """32 first, count, time, mode: the same fade to grey over `time`."""
    room = Room(console)
    room.run([op("palette_fade_grey", 0xFE, 0, 16, 0), op("exit")], frames=2)
    early = colour(room, 0x21)
    room.emu.run_frames(40)
    assert (early != (27, 27, 27), colour(room, 0x21)) == (True, (27, 27, 27))


def test_request_uploads_bit_4_sends_c400_to_cgram(console: Console) -> None:
    """69 mask: `$3B |= mask`, the vblank uploads (DA238E); bit 4 copies `$7E:C400` to CGRAM 00-7F."""
    room = Room(console)
    room.emu.write_range(0x7EC400 + 2 * 0x21, b"\x00\x7c")
    room.emu.run_frames(5)
    before = colour(room, 0x21)
    room.run([op("request_uploads", 0x10), op("exit")], frames=5)
    assert (before, colour(room, 0x21)) == ((31, 0, 0), (0, 0, 31))


WINDOW_SETUP = [op("setup_windows", 0, 0, 160, 1, 0, 1, 0, 0, 0, 0, 0, 18), op("load_window_shapes", 16)]


def window_1_rows(room: Room) -> tuple[int, int] | None:
    """First and last scanline whose window 1 differs from line 0's, in the HDMA table at `$7F:E000`."""
    table = bytes(room.emu.read_range(0x7FE000, 5 * 224))
    lines = [table[5 * i + 1 : 5 * i + 3] for i in range(224)]
    rows = [i for i, line in enumerate(lines) if line != lines[0]]
    return (rows[0], rows[-1]) if rows else None


def test_animate_window_1_draws_a_shape_at_its_centre(console: Console) -> None:
    """5C loads window shapes (`$7F:E700`, `$7F:E800`); 5D first, last, frames, mode, x, y draws frame 8 here,
    centred on (x, y) (DA5DB3)."""
    rows = []
    for y in (48, 100):
        room = Room(console)
        room.run([*WINDOW_SETUP, op("animate_window_1", 8, 8, 1, 0, 136, y), op("exit")], frames=20)
        rows.append(window_1_rows(room))
    assert rows == [(10, 52), (62, 104)]


def test_move_window_1_moves_the_shape(console: Console) -> None:
    """77 x, y, x', y', frames: the shape's centre (`$09EE`, `$09EF`) goes from (x, y) to (x', y')."""
    room = Room(console)
    moving = [op("animate_window_1", 8, 8, 1, 0, 136, 48), op("move_window_1", 136, 48, 136, 100, 16)]
    room.run([*WINDOW_SETUP, *moving, op("exit")], frames=40)
    assert window_1_rows(room) == (62, 104)


def test_window_1_on_ends_the_shape(console: Console) -> None:
    """74 1 stops the animation and puts back the plain 5B window on every line (DA1DB6)."""
    room = Room(console)
    room.run([*WINDOW_SETUP, op("animate_window_1", 0, 8, 32, 0, 136, 100), op("exit")], frames=20)
    drawn = window_1_rows(room)
    room.run([op("window_1", 1), op("exit")], frames=5)
    assert (drawn is not None, window_1_rows(room)) == (True, None)


def test_set_mosaic_sets_its_register(console: Console) -> None:
    """2D size, layers: `$6E` = size << 4 | layers, MOSAIC every vblank (DA03E6)."""
    room = Room(console)
    written = []
    room.emu.add_write_callback(0x2106, 0x2106, lambda address, value: written.append(value))
    room.run([op("set_mosaic", 13, 0x07), op("exit")], frames=5)
    assert written[-1] == 0xD7


def test_fade_mosaic_ends_on_its_target(console: Console) -> None:
    """2C from, to, frames, layers << 4 | mode."""
    room = Room(console)
    room.run([op("fade_mosaic", 0, 13, 16, 0x70), op("exit")], frames=40)
    assert room.byte(0x7E006E) == 0xD7


def sound_volumes(room: Room) -> list[int]:
    return [voice.vol_l for voice in room.emu.dsp_voices()]


def test_music_volume_silences_the_music_voices(console: Console) -> None:
    """6C 0, volume: driver command 13 sends SPC 1B: the music voices (0-5 on this field) take the volume at once;
    6C n, volume (SPC 13) steps towards it every n ticks."""
    room = Room(console)
    room.run([op("music_volume", 0, 0), op("exit")], frames=5)
    assert sound_volumes(room)[:6] == [0] * 6


def test_sfx_volume_silences_the_sound_effects(console: Console) -> None:
    """6F 0, volume: SPC 1A, the effect voices (6, 7); the music plays on."""
    room = Room(console)
    room.run([op("sfx_volume", 0, 0), op("wait_frames", 10), op("play_sound", 0x0B), op("exit")], frames=20)
    volumes = sound_volumes(room)
    assert (volumes[6:], all(volumes[1:4])) == ([0, 0], True)


def test_music_tempo_sets_the_spc_timer_offset(console: Console) -> None:
    """92 0, offset: SPC 19, `$5E` = offset, timer 0 period = the song's (`$5D`) + offset (bigger is slower)."""
    room = Room(console)
    room.run([op("music_tempo", 0, 0x40), op("exit")], frames=5)
    assert bytes(room.emu.aram_read())[0x5E] == 0x40


def test_pad_during_scripts_lets_the_player_walk_while_a_script_runs(console: Console) -> None:
    """71 1 sets `$40` bit 7: the pad handler (DA2C9C) runs even while a script does (`$3F` bit 0)."""
    rows = []
    for on in (0, 1):
        room = Room(console)
        room.run([op("pad_during_scripts", on), op("wait_frames", 120), op("exit")], frames=5)
        y = room.word(CAMERA_Y) + room.word(PLAYER_Y)
        room.emu.press(0, room.console.button.DOWN)
        room.emu.run_frames(40)
        room.emu.release(0, room.console.button.DOWN)
        room.emu.run_frames(20)
        rows.append((room.word(CAMERA_Y) + room.word(PLAYER_Y) - y) > 0)
    assert rows == [False, True]


def test_bg2_sway_scrolls_bg2_line_by_line(console: Console) -> None:
    """72 first, middle, last line, speed.w, speed.w, period: HDMA channel 1 writes BG2HOFS per line from
    `$7F:E000` (DA1DF6), lines first-last moving at their own speed (task 11, DA33CA)."""
    room = Room(console)
    room.run([op("bg2_sway", 32, 96, 160, 2048, 0, 240), op("exit")], frames=60)
    table = bytes(room.emu.read_range(0x7FE000, 3 * 224))
    offsets = {int.from_bytes(table[3 * i + 1 : 3 * i + 3], "little") for i in range(32, 160)}
    assert (room.emu.read(0x4311), room.byte(0x7E006C) & 0x02, len(offsets) > 10) == (0x0F, 0x02, True)


def text_wait(room: Room, end: int) -> tuple[int, int]:
    """Room bit 1 after the text printed, before and after an A press."""
    text = [op("open_window", 1), op("display_text", "text"), op("set_room_bits", 1), op("close_window"), op("exit")]
    room.run([*text, "text", bytes([0x20, 0x21, end])], frames=60)
    before = room.byte(ROOM_BITS) & 1
    room.console.tap(room.console.button.A)
    room.emu.run_frames(30)
    return before, room.byte(ROOM_BITS) & 1


def test_ff_ends_a_text_on_a_key_press(console: Console) -> None:
    """display_dialog_string (DA3AFE): FF prints the line, waits for a key (DA3EEC), ends."""
    assert text_wait(Room(console), 0xFF) == (0, 1)


def test_fd_ends_a_text_without_waiting(console: Console) -> None:
    assert text_wait(Room(console), 0xFD) == (1, 1)
