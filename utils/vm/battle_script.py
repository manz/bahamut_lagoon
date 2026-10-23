"""Decoder for the battle event scripts: the VM at C0:6F00 (`battle_opcode_runner`, dispatch table C0:7C07).

A battle room (24-bit pointers at C7:140F, one per scenario) is an LZ stream (`utils.dump_battle_rooms`) unpacked to
$7F:C080. Its first word is the offset of the script: what comes before it is map data (event tile changes at
$7F:C282, ...). C0:7522 sets the script base `$32` = $C080 + that word; every address operand is relative to it.

Script header, at the base:

- 0x00-0x1B: 14 entry words, run by C0:6ED8 (index = entry). The battle calls them on its events (stubs C0:6E52 -
  C0:6ED3: start, phases, unit actions; which is which is not mapped yet).
- 0x1C: the area-trigger table (C0:68E0): 5-byte records `x, y, w, h, flag` up to a negative x. A unit stopping in
  the rectangle sets the local flag (clears it when `flag` bit 7 is set).
- 0x1E: the text table, words indexed by `say_index` (23) / `load_text_index` (28).

VM state ($7E:1A00-): `$1A00` program counter, `$1A02` 16-bit register (`reg`, most results land there, FF = none),
`$1A04` the P flags of the last compare / arithmetic (Z, N, C read by the conditional jumps), `$1A08` / `$1A20`
loop stack (8 entries), `$1A09` / `$1A40` call stack (8 entries), `$1AC0` 256 local flags.

Elsewhere: 0x60 variables at $7E:3F90 (`load_var` / `store_var`; bit 7 of the operand = word), whose 0x40-0x5F are
the 256 battle flags (`set_flag`, `jump_if_flag`); 128 room flags at $7F:C000 (`set_room_flag`, `jump_if_room_flag`).
A unit operand of FF means the unit in `reg`. Unit 0-0B are the player's, 0C-1B the enemy's.

Operand kinds: b byte, w word, j code address, t text address, i text index. Every handler was read:
docs/vm/battle_opcodes.md has what each does and how sure.

    uv run python -m utils.vm.battle_script ROOM
"""

from __future__ import annotations

from dataclasses import dataclass

ENTRIES = 14
AREA_TABLE = 0x1C
TEXT_TABLE = 0x1E

# opcode: (name, operand kinds)
OPS: dict[int, tuple[str, str]] = {
    0x00: ("jump", "j"),
    0x01: ("jump_if_equal", "j"),
    0x02: ("jump_if_negative", "j"),
    0x03: ("jump_if_positive", "j"),
    0x04: ("nop", ""),
    0x05: ("jump_if_not_equal", "j"),
    0x06: ("jump_if_none", "j"),
    0x07: ("wait", "b"),
    0x08: ("loop_start", "b"),
    0x09: ("loop_end", ""),
    0x0A: ("call", "j"),
    0x0B: ("return", ""),
    0x0C: ("jump_if_carry", "j"),
    0x0D: ("jump_if_no_carry", "j"),
    0x0E: ("jump_if_local_flag", "bj"),
    0x0F: ("jump_unless_local_flag", "bj"),
    0x10: ("compare", "b"),
    0x11: ("test_bits", "b"),
    0x12: ("increment", ""),
    0x13: ("decrement", ""),
    0x14: ("add", "b"),
    0x15: ("subtract", "b"),
    0x16: ("load", "b"),
    0x17: ("load_word", "w"),
    0x18: ("load_turn", ""),
    0x19: ("load_current_unit", ""),
    0x1A: ("load_unit_field", "b"),
    0x1B: ("find_member_slot", "b"),
    0x1C: ("select_unit_reg", ""),
    0x1D: ("select_unit", "b"),
    0x1E: ("load_3bd8", ""),
    0x1F: ("swap_bytes", ""),
    0x20: ("open_window", ""),
    0x21: ("open_window_1", ""),
    0x22: ("close_window", ""),
    0x23: ("say_index", "i"),
    0x24: ("clear_window", ""),
    0x25: ("open_window_a0", ""),
    0x26: ("say", "t"),
    0x27: ("ask", "t"),
    0x28: ("load_text_index", "i"),
    0x29: ("load_text", "t"),
    0x2A: ("set_text_arg", "bb"),
    0x2B: ("set_text_arg_word", "bw"),
    0x2C: ("say_loaded", ""),
    0x30: ("skip_2", "bb"),
    0x31: ("move_cursor_to", "bbb"),
    0x33: ("set_enemy_order", "bb"),
    0x35: ("move_cursor", "b"),
    0x36: ("grab_unit", ""),
    0x37: ("drop_unit", ""),
    0x38: ("unit_walk_off", "b"),
    0x39: ("remove_unit", ""),
    0x3A: ("check_unit", "b"),
    0x3B: ("spawn_unit", "b"),
    0x40: ("set_mode_10", ""),
    0x41: ("clear_mode_10", ""),
    0x42: ("focus_unit", ""),
    0x43: ("scroll_view", "bb"),
    0x44: ("shake_screen", "b"),
    0x45: ("stop_shake", ""),
    0x50: ("jump_if_room_flag", "bj"),
    0x51: ("jump_unless_room_flag", "bj"),
    0x52: ("jump_if_flag", "bj"),
    0x53: ("jump_unless_flag", "bj"),
    0x54: ("call_if_equal", "j"),
    0x55: ("call_if_not_equal", "j"),
    0x56: ("return_if_equal", ""),
    0x57: ("return_if_not_equal", ""),
    0x60: ("set_flag", "b"),
    0x61: ("clear_flag", "b"),
    0x62: ("load_var", "b"),
    0x63: ("store_var", "b"),
    0x64: ("load_event_arg", ""),
    0x65: ("load_event_word", ""),
    0x66: ("test_area_units", "bbbb"),
    0x67: ("test_unit_tile", "b"),
    0x68: ("load_tile_unit", "bb"),
    0x69: ("test_unit_area", "bbb"),
    0x6A: ("test_area_terrain", "bbbb"),
    0x6B: ("load_terrain", "bb"),
    0x6C: ("test_unit_area_vars", ""),
    0x6D: ("test_area_terrain_vars", ""),
    0x6E: ("queue_scripted_action", "bbbbbbb"),
    0x90: ("load_unit_position", "b"),
    0x91: ("load_unit_byte", "bb"),
    0x92: ("find_enemy_flag_4", ""),
    0xF0: ("map_event", "b"),
    0xF1: ("sound_command", "bbbb"),
    0xF2: ("load_sound_byte", "b"),
    0xF3: ("give_item", "bb"),
    0xF4: ("set_room_flag", "b"),
    0xF5: ("map_event_f5", "b"),
    0xF6: ("refresh_map", ""),
    0xF7: ("unit_marker", "bb"),
    0xF8: ("set_unit_sprite", "bb"),
    0xF9: ("restore_unit_sprite", "b"),
    0xFF: ("exit", ""),
}
# Every other opcode dispatches to the nop handler (C0:6F74), like 04.
UNUSED = tuple(op for op in range(0x100) if op not in OPS)

JUMPS = {"jump", "call", "call_if_equal", "call_if_not_equal"} | {n for n, _ in OPS.values() if n.startswith("jump_")}
STOPS = {"jump", "return", "exit"}  # no fall-through
CALLS = {"call", "call_if_equal", "call_if_not_equal"}
TEXTS = {"say", "ask", "load_text"}  # a text address operand
TEXT_INDEXES = {"say_index", "load_text_index"}


def name(op: int) -> str:
    return OPS[op][0] if op in OPS else f"unused_{op:02x}"


def kinds(op: int) -> str:
    return OPS[op][1] if op in OPS else ""


def size(op: int) -> int:
    return 1 + sum(2 if k in "wjt" else 1 for k in kinds(op))


def word(data: bytes, pos: int) -> int:
    return data[pos] | data[pos + 1] << 8


@dataclass(frozen=True)
class Header:
    entries: tuple[int, ...]
    area_table: int
    text_table: int

    def text(self, data: bytes, index: int) -> int:
        """The address of text `index` of the text table."""
        return word(data, self.text_table + 2 * index)


def header(data: bytes) -> Header:
    return Header(tuple(word(data, 2 * k) for k in range(ENTRIES)), word(data, AREA_TABLE), word(data, TEXT_TABLE))


@dataclass(frozen=True)
class Instruction:
    op: int
    args: tuple[int, ...]
    size: int

    @property
    def name(self) -> str:
        return name(self.op)

    @property
    def targets(self) -> list[int]:
        """Code addresses this instruction may continue at besides the next one."""
        return [self.args[-1]] if self.name in JUMPS else []

    @property
    def text(self) -> int | None:
        return self.args[-1] if self.name in TEXTS else None

    @property
    def text_index(self) -> int | None:
        return self.args[0] if self.name in TEXT_INDEXES else None

    def __str__(self) -> str:
        shown = []
        for kind, arg in zip(kinds(self.op), self.args, strict=True):
            shown.append(f"@{arg:04x}" if kind in "jt" else f"{arg:#04x}" if kind == "w" else f"{arg:#02x}")
        return f"{self.name}({', '.join(shown)})"


def instruction(data: bytes, pos: int) -> Instruction:
    op = data[pos]
    args, at = [], pos + 1
    for kind in kinds(op):
        if kind in "wjt":
            args.append(word(data, at))
            at += 2
        else:
            args.append(data[at])
            at += 1
    return Instruction(op, tuple(args), at - pos)


def main(argv: list[str] | None = None) -> None:
    import argparse

    from utils.battle_walk import room_script, walk

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("room", type=int)
    args = parser.parse_args(argv)
    data = room_script(args.room)
    w = walk(data)
    for pos in sorted(w.code):
        label = "*" if pos in w.labels else " "
        print(f"{label}{pos:04x}: {w.code[pos]}")


if __name__ == "__main__":
    main()
