"""Walk the dialog room scripts from every place the game enters them, and report what the walk never reaches.

Entry points (the header words, docs/vm/dialog_opcodes.md):

- +0 the start-up script (its offset is also the header's length);
- +4 position triggers: (x, y, flags, script) records up to an FFFF word;
- +6 actor events: a script per actor of the +2 table (talked to, or touched), by actor id, up to an FFFF word;
- +8 the timer script, +C the skip script (Start, once allowed), each when not 0;
- +A area triggers: (x1, y1, x2, y2, flags, script) records up to an FFFF word.

From each, the walk follows every jump, call and branch target and falls through what does not stop. Bytes it
accounts for: the header and its tables, the actor records, every reached instruction, the texts and palette data
those instructions point at. What is left is code no entry runs (or data nothing points at).

    uv run python -m utils.vm.room_walk [ROOM ...] [--rom build/bl.sfc]
"""

import argparse
from collections.abc import Callable
from dataclasses import dataclass, field
from io import BufferedReader
from pathlib import Path

from utils.cartridge import rom_offset
from utils.dump_rooms import decompress_block, is_compressed
from utils.vm.room_ops import DecodeError, Instruction, decode

ROOMS = 0xFF
ROOM_POINTERS = 0xDA8000
ACTOR_RECORD = 7  # bytes of an actor record of the +2 table
MAX_ACTORS = 0x17
TRIGGER_TABLES = {0x04: (5, 3), 0x0A: (7, 5)}  # header word: (record size, offset of its script word)
SINGLE_SCRIPTS = {0x08: "timer", 0x0C: "skip"}
NO_ENTRY = 0xFFFF


def word(data: bytes, pos: int) -> int:
    return int.from_bytes(data[pos : pos + 2], "little")


def text_length(data: bytes, pos: int) -> int:
    """A string's bytes, up to and including its end (FF, or FD; FF FF and FD FF count both), as the text dumper
    reads it (utils.vm.opcodes.get_string_from_room)."""
    end = pos
    while end < len(data):
        if data[end : end + 2] in (b"\xff\xff", b"\xfd\xff"):
            return end + 2 - pos
        if data[end] in (0xFF, 0xFD):
            return end + 1 - pos
        end += 1
    return len(data) - pos


@dataclass(frozen=True)
class Entry:
    """A script entry point of the header: what starts it, and its offset."""

    what: str
    offset: int


@dataclass
class Walk:
    data: bytes
    code: dict[int, Instruction] = field(default_factory=dict)
    covered: dict[int, int] = field(default_factory=dict)  # offset -> length of non-code bytes accounted for
    entries: list[Entry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def header_length(self) -> int:
        return word(self.data, 0)

    def mark(self, pos: int, length: int) -> None:
        if 0 <= pos < len(self.data) and length > 0:
            self.covered[pos] = max(self.covered.get(pos, 0), min(length, len(self.data) - pos))

    def has(self, offset: int) -> bool:
        return offset + 2 <= self.header_length

    def spans(self) -> list[tuple[int, int]]:
        spans = [(o, o + i.size) for o, i in self.code.items()]
        spans += [(o, o + n) for o, n in self.covered.items()]
        return sorted(spans)

    def unreached(self) -> list[tuple[int, int]]:
        """Offset ranges [start, end) nothing the walk accounted for covers."""
        gaps, at = [], 0
        for lo, hi in self.spans():
            if lo > at:
                gaps.append((at, lo))
            at = max(at, hi)
        if at < len(self.data):
            gaps.append((at, len(self.data)))
        return gaps

    def reached_bytes(self) -> int:
        return len(self.data) - sum(hi - lo for lo, hi in self.unreached())


def actor_count(walk: Walk) -> int:
    if not walk.has(0x02):
        return 0
    table = word(walk.data, 0x02)
    count = 0
    while count < MAX_ACTORS and table + 2 * count + 2 <= len(walk.data):
        record = word(walk.data, table + 2 * count)
        walk.mark(table + 2 * count, 2)
        if record == NO_ENTRY:
            break
        walk.mark(record, ACTOR_RECORD)
        count += 1
    return count


def trigger_roots(walk: Walk, header: int, size: int, script: int) -> list[Entry]:
    table = word(walk.data, header)
    if table == 0:
        return []
    roots, at = [], table
    while at + 2 <= len(walk.data) and word(walk.data, at) != NO_ENTRY:
        walk.mark(at, size)
        fields = ", ".join(str(walk.data[at + i]) for i in range(script))
        roots.append(Entry(f"+{header:X} trigger ({fields}) at {at:04x}", word(walk.data, at + script)))
        at += size
    walk.mark(at, 2)
    return roots


def event_roots(walk: Walk, actors: int) -> list[Entry]:
    """The +6 table: a script per actor, by actor id, up to an FFFF word (actors past it have none)."""
    table = word(walk.data, 0x06)
    roots = []
    for actor in range(actors + 1):
        walk.mark(table + 2 * actor, 2)
        entry = word(walk.data, table + 2 * actor)
        if entry == NO_ENTRY:
            break
        roots.append(Entry(f"+6 actor {actor} event", entry))
    return roots


def entry_points(walk: Walk) -> list[Entry]:
    """Every script entry point of the room's header, in header order."""
    walk.mark(0, walk.header_length)
    found = [Entry("+0 start-up", walk.header_length)]
    actors = actor_count(walk)
    for header, (size, script) in TRIGGER_TABLES.items():
        if walk.has(header):
            found += trigger_roots(walk, header, size, script)
    if walk.has(0x06):
        found += event_roots(walk, actors)
    found += [
        Entry(f"+{h:X} {SINGLE_SCRIPTS[h]}", word(walk.data, h))
        for h in SINGLE_SCRIPTS
        if walk.has(h) and word(walk.data, h) != 0
    ]
    return found


def follow(walk: Walk, pos: int) -> None:
    """Decode from pos while the code falls through, queueing every target."""
    todo = [pos]
    while todo:
        at = todo.pop()
        while 0 <= at < len(walk.data) and at not in walk.code:
            try:
                ins = decode(walk.data, at)
            except DecodeError as error:
                walk.errors.append(str(error))
                break
            walk.code[at] = ins
            todo += ins.targets
            for text in ins.texts:
                walk.mark(text, text_length(walk.data, text))
            for offset, length in ins.data:
                walk.mark(offset, length)
            if not ins.falls_through:
                break
            at += ins.size


def walk_room(data: bytes) -> Walk:
    walk = Walk(data)
    walk.entries = entry_points(walk)
    for entry in walk.entries:
        follow(walk, entry.offset)
    return walk


def room_data(rom: BufferedReader, room: int) -> bytes | None:
    """A compressed room, decompressed; None for the rooms stored raw (no script)."""
    if not is_compressed(rom, room):
        return None
    rom.seek(rom_offset(ROOM_POINTERS) + room * 3)
    pointer = int.from_bytes(rom.read(3), "little")
    rom.seek(rom_offset(pointer))
    return bytes(decompress_block(rom))


def linear_ops(data: bytes, lo: int, hi: int) -> int | None:
    """How many instructions [lo, hi) decodes into end to end, None when it does not (data, or a cut)."""
    count, at = 0, lo
    while at < hi:
        try:
            at += decode(data, at).size
        except DecodeError:
            return None
        count += 1
    return count if at == hi else None


def report(room: int, walk: Walk) -> list[str]:
    total = len(walk.data)
    reached = walk.reached_bytes()
    lines = [f"room {room:3d}: {reached}/{total} bytes reached ({100 * reached / total:.1f}%), {len(walk.code)} ops"]
    for lo, hi in walk.unreached():
        ops = linear_ops(walk.data, lo, hi)
        what = f", decodes as {ops} ops" if ops else ""
        lines.append(f"  unreached {lo:04x}-{hi - 1:04x} ({hi - lo} bytes){what}")
    lines += [f"  error: {error}" for error in walk.errors]
    return lines


def main(argv: list[str] | None = None, echo: Callable[[str], None] = print) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rooms", type=int, nargs="*")
    parser.add_argument("--rom", type=Path, default=Path("build/bl.sfc"), help="the Japanese ROM")
    args = parser.parse_args(argv)
    reached = total = 0
    with open(args.rom, "rb") as rom:
        for room in args.rooms or range(ROOMS):
            data = room_data(rom, room)
            if data is None:
                continue
            walk = walk_room(data)
            reached, total = reached + walk.reached_bytes(), total + len(data)
            for line in report(room, walk):
                echo(line)
    echo(f"all: {reached}/{total} bytes reached ({100 * reached / total:.1f}%)")


if __name__ == "__main__":
    main()
