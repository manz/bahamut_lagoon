"""
Room script opcodes checked in game (docs/vm/dialog_opcodes.md, the ✓ marks): on the field after New Game
(new-game-field, room 0 idle), a script written past the room's end in its buffer runs as the header's +C script,
which the field loop starts when `$41` bit 4 is set (DA043C). Room bits (`$0312`, opcode 62) say which way it went.
"""

from tests.conftest import Console

ROOM_POINTER = 0x7E0067  # [$67]: the room's start, its buffer in bank 7F
ROOM_BITS = 0x7E0312
ROOM_EVENTS = 0x7E0041  # bit 3: Start runs the +C script (opcode 7C), bit 4: run it now
SCRIPT_AT = 0x1400  # past room 0's 0x12CB bytes
TIMER_SCRIPT_AT = 0x1440
SKIP_SCRIPT_AT = 0x1480
ROOM_BYTES = 0x7E3BD0  # set_var / add_var table 4: a byte array indexed by the field operand alone


class Room:
    def __init__(self, console: Console) -> None:
        console.load("new-game-field")
        self.console = console
        self.emu = console.emu
        self.base = int.from_bytes(bytes(self.emu.read_range(ROOM_POINTER, 3)), "little")

    def byte(self, address: int) -> int:
        return bytes(self.emu.read_range(address, 1))[0]

    def put(self, at: int, script: str) -> None:
        self.emu.write_range(self.base + at, bytes.fromhex(script))

    def header(self, offset: int, at: int) -> None:
        self.emu.write_range(self.base + offset, at.to_bytes(2, "little"))

    def run(self, script: str, frames: int = 30) -> None:
        """Run script once as the +C script."""
        self.put(SCRIPT_AT, script)
        self.header(0x0C, SCRIPT_AT)
        self.emu.write_range(ROOM_EVENTS, bytes([self.byte(ROOM_EVENTS) | 0x10]))
        self.emu.run_frames(frames)


def test_add_var_clamped_clamps_to_its_maximum(console: Console) -> None:
    """90: table 4 skips the record byte (77 here); 4 + 5 clamped to 7."""
    room = Room(console)
    room.emu.write_range(ROOM_BYTES + 0x10, b"\x04")
    room.run("90 04 77 10 05 00 07 ff")
    assert room.byte(ROOM_BYTES + 0x10) == 7


def test_add_var_clamped_clamps_to_its_minimum(console: Console) -> None:
    """90: 4 + FE wraps to 2, raised to the minimum 3."""
    room = Room(console)
    room.emu.write_range(ROOM_BYTES + 0x10, b"\x04")
    room.run("90 04 00 10 fe 03 07 ff")
    assert room.byte(ROOM_BYTES + 0x10) == 3


def test_the_timer_runs_the_header_8_script_when_it_runs_out(console: Console) -> None:
    """40 sets the countdown (frames), 41 starts it; at 0 the field runs the +8 script."""
    room = Room(console)
    room.put(TIMER_SCRIPT_AT, "62 02 ff")
    room.header(0x08, TIMER_SCRIPT_AT)
    room.run("40 3c 00 41 01 ff", frames=20)
    early = room.byte(ROOM_BITS) & 0x02
    room.emu.run_frames(80)
    assert (early, room.byte(ROOM_BITS) & 0x02) == (0, 0x02)


def test_start_runs_the_skip_script_once_allowed(console: Console) -> None:
    """7C 01 lets Start run the +C script."""
    room = Room(console)
    room.run("7c 01 ff")
    room.put(SKIP_SCRIPT_AT, "62 04 ff")
    room.header(0x0C, SKIP_SCRIPT_AT)
    before = room.byte(ROOM_BITS) & 0x04
    console.tap(console.button.START)
    assert (before, room.byte(ROOM_BITS) & 0x04) == (0, 0x04)


def test_open_menu_hands_its_kind_to_the_system_bank(console: Console) -> None:
    """45 kind 6 goes through the EE3018 vector: menu 7 in `$05FC`, the argument in `$05FE`."""
    room = Room(console)
    room.emu.write_range(0x7E05FC, bytes(4))
    room.run("45 06 03 ff", frames=10)
    assert bytes(room.emu.read_range(0x7E05FC, 4)) == bytes.fromhex("07000300")
