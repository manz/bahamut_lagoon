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
CAMERA_Y = 0x7E037E
PLAYER_Y = 0x7E0702
WALKER_X = 0x7E0764
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
    room.run([op("set_word_0329", 60), op("set_state_3c_80", 1), op("exit")], frames=20)
    early = room.byte(ROOM_BITS) & 0x02
    room.emu.run_frames(80)
    assert (early, room.byte(ROOM_BITS) & 0x02) == (0, 0x02)


def test_start_runs_the_skip_script_once_allowed(console: Console) -> None:
    """7C 01 lets Start run the +C script."""
    room = Room(console)
    room.run([op("set_state_41_08", 1), op("exit")])
    room.put(SKIP_SCRIPT_AT, [op("set_room_bits", 0x04), op("exit")])
    room.header(0x0C, SKIP_SCRIPT_AT)
    before = room.byte(ROOM_BITS) & 0x04
    console.tap(console.button.START)
    assert (before, room.byte(ROOM_BITS) & 0x04) == (0, 0x04)


def test_open_menu_hands_its_kind_to_the_system_bank(console: Console) -> None:
    """45 kind 6 goes through the EE3018 vector: menu 7 in `$05FC`, the argument in `$05FE`."""
    room = Room(console)
    room.emu.write_range(0x7E05FC, bytes(4))
    room.run([op("set_state_0327", 6, 3), op("exit")], frames=10)
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


def test_actor_set_b811_offsets_the_sprite(console: Console) -> None:
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


def test_set_state_3c_20_off_stops_the_camera_following(console: Console) -> None:
    """28 0 sets `$3C` bit 5: the walk step (DA1FF2) no longer scrolls the camera."""
    assert camera_after_walking_down(Room(console), [op("camera_follow", 0)]) == 0x10


def test_set_layer_position_limits_the_camera(console: Console) -> None:
    """7F x, y: the camera's largest x, y (`$0394`, `$0396`, in tiles), which a followed walk clamps to (DA2FE1)."""
    assert camera_after_walking_down(Room(console), [op("camera_limit", 0x10, 3)]) == 0x30


def test_set_state_41_40_lets_the_camera_past_its_limit(console: Console) -> None:
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


def test_actor_set_b813_keeps_the_player_in_a_box(console: Console) -> None:
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
