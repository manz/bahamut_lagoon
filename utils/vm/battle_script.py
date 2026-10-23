"""Decoder for the battle event scripts: the VM at C0:6F00 (`battle_opcode_runner`, dispatch table C0:7C07).

A battle room (24-bit pointers at C7:140F, one per scenario) is an LZ stream (`utils.dump_battle_rooms`) unpacked to
$7F:C080. Its first word is the offset of the script: what comes before it is map data (event tile changes at
$7F:C282, ...). C0:7522 sets the script base `$32` = $C080 + that word; every address operand is relative to it.

Script header, at the base:

- 0x00-0x1B: 14 entry words, run by C0:6ED8 (index = entry). The battle calls them on its events (stubs C0:6E52 -
  C0:6ED3; ENTRY_NAMES says which).
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

    uv run python -m utils.vm.battle_script ROOM [--fr] [--bytes]

lists a room's script: the header entries named by when the battle runs them, labels on jump targets, the texts
decoded (vanilla ROM, or the French build with --fr). utils.vm.battle_asm encodes it back.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

from katsuji.script import Table

ENTRIES = 14
# Header entries by index: label, when the battle runs it (docs/vm/battle_opcodes.md).
ENTRY_NAMES: tuple[tuple[str, str], ...] = (
    ("turn_start", "turn start, before C0:5ED4 / A241 (skipped while $1ABF = 2)"),
    ("turn_start_2", "turn start, after C0:A241"),
    ("player_phase", "the player phase starts; var 28 = 0 after it"),
    ("player_phase_end", "the player phase is over, dragons included"),
    ("turn_end", "end of the turn, before the turn number steps"),
    ("victory", "the battle is won, before the experience window"),
    ("unused_06", "never run: nothing calls it"),
    ("player_moved", "a player-side unit (dragons too) ended its move"),
    ("player_acted", "after a player-side action"),
    ("unit_defeated", "a unit was defeated, either side"),
    ("enemy_moved", "an enemy unit ended its move"),
    ("enemy_acted", "after an enemy action"),
    ("before_action", "before an action, either side"),
    ("after_victory", "after the experience window, last before the battle ends"),
)
HEADER_SIZE = 0x20
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
    0x1B: ("find_character_unit", "b"),
    0x1C: ("select_unit_reg", ""),
    0x1D: ("select_unit", "b"),
    0x1E: ("load_scenario", ""),
    0x1F: ("swap_bytes", ""),
    0x20: ("open_window", ""),
    0x21: ("open_window_top", ""),
    0x22: ("close_window", ""),
    0x23: ("say_index", "i"),
    0x24: ("clear_window", ""),
    0x25: ("open_window_bottom", ""),
    0x26: ("say", "t"),
    0x27: ("ask", "t"),
    0x28: ("load_text_index", "i"),
    0x29: ("load_text", "t"),
    0x2A: ("set_text_arg", "bb"),
    0x2B: ("set_text_arg_word", "bw"),
    0x2C: ("say_loaded", ""),
    0x30: ("skip_2", "bb"),
    0x31: ("use_action_at", "bbb"),
    0x33: ("set_enemy_order", "bb"),
    0x35: ("move_cursor", "b"),
    0x36: ("grab_unit", ""),
    0x37: ("drop_unit", ""),
    0x38: ("unit_walk_off", "b"),
    0x39: ("remove_unit", ""),
    0x3A: ("check_unit", "b"),
    0x3B: ("spawn_unit", "b"),
    0x40: ("hide_cursor", ""),
    0x41: ("show_cursor", ""),
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
    0x64: ("load_action", ""),
    0x65: ("load_action_attributes", ""),
    0x66: ("test_area_in_range", "bbbb"),
    0x67: ("test_unit_in_range", "b"),
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


@dataclass(frozen=True)
class Data:
    """Bytes the walk does not run: `kind` dead (unreached code), areas, text_table or text."""

    raw: bytes
    kind: str


Item = Instruction | Data


@dataclass(frozen=True)
class Disassembly:
    header: Header
    items: tuple[tuple[int, Item], ...]  # (offset, item) from the header's end to the script's end, in order
    labels: frozenset[int]  # entries and jump targets
    texts: frozenset[int]  # text addresses the code shows


def disassemble(data: bytes) -> Disassembly:
    """The whole script after the header: the instructions the walk reaches, the rest as data."""
    from utils.battle_walk import walk

    w = walk(data)
    head = header(data)
    tail_cuts = sorted({w.code_end(), head.area_table, head.text_table, len(data)} | w.texts)
    items: list[tuple[int, Item]] = []
    for lo, hi in _gaps(w.code, HEADER_SIZE, w.code_end()):
        items.append((lo, Data(data[lo:hi], "dead")))
    items += w.code.items()
    for lo, hi in pairwise(tail_cuts):
        if lo >= w.code_end() and hi > lo:
            kind = "areas" if lo == head.area_table else "text" if lo in w.texts else "text_table"
            items.append((lo, Data(data[lo:hi], kind)))
    items.sort(key=lambda item: item[0])
    return Disassembly(head, tuple(items), frozenset(w.labels), frozenset(w.texts))


def _gaps(code: dict[int, Instruction], start: int, end: int) -> Iterator[tuple[int, int]]:
    at = start
    for lo in sorted(code):
        if lo > at:
            yield at, lo
        at = max(at, lo + code[lo].size)
    if at < end:
        yield at, end


# Text control codes and their argument bytes (display_battle_text); FE a new line, FD waits, FF ends.
CONTROL_ARGS = {0xF4: 1, 0xF5: 1, 0xF6: 1, 0xF7: 1, 0xF8: 1, 0xF9: 2, 0xFA: 1, 0xFC: 1}
PREFIXES = range(0xF0, 0xF4)  # vanilla: the font page of the characters after it
TABLES = Path(__file__).parents[2] / "text/table"


@dataclass(frozen=True)
class TextCodec:
    """Battle text to a readable string: vanilla codes are a page prefix (F0-F3) and a byte, French ones a byte."""

    table: Table
    paged: bool

    @classmethod
    def for_rom(cls, french: bool) -> TextCodec:
        return cls(Table(str(TABLES / ("mz.tbl" if french else "jp.tbl"))), paged=not french)

    def decode(self, data: bytes, at: int) -> str:
        out, page = [], 0xF0
        while at < len(data) and data[at] != 0xFF:
            code = data[at]
            if code in CONTROL_ARGS:
                args = data[at + 1 : at + 1 + CONTROL_ARGS[code]]
                out.append(f"[{code:02x} {args.hex(' ')}]")
                at += 1 + CONTROL_ARGS[code]
                continue
            if self.paged and code in PREFIXES:
                page = code
            elif code == 0xFE:
                out.append("\\n")
            elif code == 0xFD:
                out.append("[wait]")
            else:
                out.append(self.table.to_text(bytes([page, code]) if self.paged else bytes([code])).replace("\\s", " "))
            at += 1
        return "".join(out)


def label(offset: int, entries: dict[int, list[int]]) -> str:
    return ENTRY_NAMES[entries[offset][0]][0] if offset in entries else f"L_{offset:04x}"


def listing(data: bytes, codec: TextCodec, show_bytes: bool = False) -> list[str]:
    dis = disassemble(data)
    entries: dict[int, list[int]] = {}
    for index, at in enumerate(dis.header.entries):
        entries.setdefault(at, []).append(index)
    lines = [f"; {len(data):#x} bytes: header, code, area triggers @{dis.header.area_table:04x}, texts"]
    for index, at in enumerate(dis.header.entries):
        lines.append(f"  {2 * index:04x}  entry {index:02x} -> {label(at, entries):<17} ; {ENTRY_NAMES[index][1]}")
    lines.append(f"  {AREA_TABLE:04x}  areas @{dis.header.area_table:04x}")
    lines.append(f"  {TEXT_TABLE:04x}  text_table @{dis.header.text_table:04x}")
    for at, item in dis.items:
        if at in dis.labels or at in dis.texts or isinstance(item, Data) and item.kind != "text":
            lines += ["", f"{_heading(at, item, entries)}:"]
        for where, size, line in _render(data, at, item, codec, entries):
            raw = f" {data[where : where + size].hex(' '):<24}" if show_bytes else ""
            lines.append(f"  {where:04x}{raw}  {line}")
    return lines


def _heading(at: int, item: Item, entries: dict[int, list[int]]) -> str:
    if isinstance(item, Data):
        return f"text_{at:04x}" if item.kind == "text" else item.kind
    name = label(at, entries)
    if at in entries:
        names = ", ".join(ENTRY_NAMES[i][0] for i in entries[at])
        return f"{name}  ; {names}" if len(entries[at]) > 1 else name
    return name


def _render(
    data: bytes, at: int, item: Item, codec: TextCodec, entries: dict[int, list[int]]
) -> list[tuple[int, int, str]]:
    """(offset, size, text) lines for one item."""
    # isinstance on Data: run as __main__, this module's Instruction is not the one utils.battle_walk decodes with.
    if isinstance(item, Data):
        if item.kind == "areas":
            return [(at + lo, size, line) for lo, size, line in _areas(item.raw)]
        if item.kind == "text":
            return [(at, len(item.raw), f'text "{codec.decode(data, at)}"')]
        return [(at, len(item.raw), f"db {item.raw.hex(' ')}")]
    shown = []
    for kind, arg in zip(kinds(item.op), item.args, strict=True):
        if kind == "j":
            shown.append(label(arg, entries))
        elif kind == "t":
            shown.append(f"text_{arg:04x}")
        else:
            shown.append(f"{arg:#06x}" if kind == "w" else f"{arg:#04x}")
    line = f"{item.name} {', '.join(shown)}".rstrip()
    if item.text is not None:
        line = f'{line:<40} ; "{codec.decode(data, item.text)}"'
    return [(at, item.size, line)]


def _areas(raw: bytes) -> list[tuple[int, int, str]]:
    lines = []
    for at in range(0, len(raw), 5):
        record = raw[at : at + 5]
        if record[0] & 0x80 or len(record) < 5:
            lines.append((at, len(raw) - at, f"db {raw[at:].hex(' ')}  ; end"))
            break
        x, y, w, h, flag = record
        verb = "clear" if flag & 0x80 else "set"
        line = f"area x={x:#04x}, y={y:#04x}, w={w:#04x}, h={h:#04x}  ; {verb} local flag {flag & 0x7F:#04x}"
        lines.append((at, 5, line))
    return lines


def main(argv: list[str] | None = None, echo: Callable[[str], None] = print) -> None:
    from utils.battle_walk import ROM, fr_rom, room_script

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("room", type=int)
    parser.add_argument("--fr", action="store_true", help="read the French build (build/bl.ips on build/bl.sfc)")
    parser.add_argument("--bytes", action="store_true", help="show each instruction's bytes")
    args = parser.parse_args(argv)
    data = room_script(args.room, fr_rom() if args.fr else ROM)
    for line in listing(data, TextCodec.for_rom(args.fr), args.bytes):
        echo(line)


if __name__ == "__main__":
    main()
