"""Operand layouts of the dialog / room script VM: the runner at DA3F00, its handlers in table DA3F20.

A room (decompressed, see docs/vm/dialog_opcodes.md) is a header of words, then code, tables and texts. Every address
in it (header words, jumps, text and data pointers) is an offset from the room's start. An instruction is an opcode
byte, then its operands; the handler returns how far the PC moves (0 when it jumped).

Operand kinds, one character each:

- `b` byte, `w` word.
- `a` 24-bit bus address (word, then bank byte).
- `j` script address (word): a jump, call or branch target.
- `t` text pointer (word): a string up to its FF or FD (`utils.vm.room_walk.text_length`).
- `p` palette data pointer (word): colours read for the palette range the operands before it chose.
- `m` a motion list up to its FF or FE (actor_move).
- `l` an actor list up to its FF (actors_hold, actors_release).

    uv run python -m utils.vm.room_ops 0x13
"""

import sys
from dataclasses import dataclass

from utils.vm.opcodes_map import opcode_names

END = 0xFF  # the runner stops on it (carry set): ends the script, or the call chain

# opcode: operand kinds. Every handler of DA3F20 read (docs/vm/dialog_opcodes.md has what each does and how sure).
OPERANDS: dict[int, str] = {
    0x00: "j",
    0x01: "bj",
    0x02: "bj",
    0x03: "bj",
    0x04: "bj",
    0x05: "j",
    0x06: "",
    0x07: "bj",
    0x08: "tjj",
    0x09: "tjjj",
    0x0A: "w",
    0x0B: "",
    0x0C: "b",
    0x0D: "b",
    0x0E: "bb",
    0x0F: "bb",
    0x10: "bb",
    0x11: "b",
    0x12: "bbb",
    0x13: "bm",
    0x14: "l",
    0x15: "bb",
    0x16: "bb",
    0x17: "bb",
    0x18: "l",
    0x19: "bb",
    0x1A: "bb",
    0x1B: "b",
    0x1C: "bb",
    0x1D: "bbb",
    0x1E: "bbw",
    0x1F: "bbw",
    0x20: "bbw",
    0x21: "bb",
    0x22: "b",
    0x23: "bb",
    0x24: "bbw",
    0x25: "bbw",
    0x26: "bbb",
    0x27: "bb",
    0x28: "b",
    0x29: "b",
    0x2A: "bbbb",
    0x2B: "b",
    0x2C: "bbbb",
    0x2D: "bb",
    0x2E: "b" * 9,
    0x2F: "b" * 6,
    0x30: "b" * 10,
    0x31: "bbb",
    0x32: "bbbb",
    0x33: "bbb",
    0x34: "bb",
    0x35: "b",
    0x36: "",
    0x37: "t",
    0x38: "",
    0x39: "b",
    0x3A: "b",
    0x3B: "b",
    0x3C: "b",
    0x3D: "w",
    0x3E: "w",
    0x3F: "b",
    0x40: "w",
    0x41: "b",
    0x42: "b",
    0x43: "b",
    0x44: "bbbb",
    0x45: "bb",
    0x46: "",
    0x47: "b",
    0x48: "b",
    0x49: "bb",
    0x4A: "bb",
    0x4B: "bb",
    0x4C: "bbb",
    0x4D: "bb",
    0x4E: "b",
    0x4F: "b",
    0x50: "jj",
    0x51: "bbp",
    0x52: "bb",
    0x53: "bb",
    0x54: "bb",
    0x55: "b" * 5,
    0x56: "bbbb",
    0x57: "bbbb",
    0x58: "bbbb",
    0x59: "aa",
    0x5A: "b",
    0x5B: "b" * 12,
    0x5C: "b",
    0x5D: "b" * 6,
    0x5E: "b" * 6,
    0x5F: "b",
    0x60: "b",
    0x61: "b",
    0x62: "b",
    0x63: "b",
    0x64: "aww",
    0x65: "aa",
    0x66: "b" * 7,
    0x67: "b",
    0x68: "aaw",
    0x69: "b",
    0x6A: "",
    0x6B: "bb",
    0x6C: "bb",
    0x6D: "b",
    0x6E: "bb",
    0x6F: "bb",
    0x70: "bbbbbj",
    0x71: "b",
    0x72: "bbbwwb",
    0x73: "b",
    0x74: "b",
    0x75: "b",
    0x76: "",
    0x77: "b" * 5,
    0x78: "b" * 5,
    0x79: "",
    0x7A: "b" * 5,
    0x7B: "t",
    0x7C: "b",
    0x7D: "bb",
    0x7E: "bb",
    0x7F: "bb",
    0x80: "b",
    0x81: "b",
    0x82: "bbbb",
    0x83: "bbb",
    0x84: "",
    0x85: "bbt",
    0x86: "",
    0x87: "",
    0x88: "b",
    0x89: "b",
    0x8A: "b",
    0x8B: "b",
    0x8C: "w",
    0x8D: "bwj",
    0x8E: "b",
    0x8F: "bb",
    0x90: "b" * 6,
    0x91: "b",
    0x92: "bb",
    0x93: "b",
    0x94: "bbj",
    END: "",
}
WIDTHS = {"b": 1, "w": 2, "a": 3, "j": 2, "t": 2, "p": 2}
LIST_ENDS = {"m": (0xFE, 0xFF), "l": (0xFF,)}  # what ends a motion list, an actor list
# No fall-through: jump, return, random_branch (one of its two targets), and the end.
STOPS = frozenset({0x00, 0x06, 0x50, END})
# Palette ranges (first colour, count) behind the FF / FE / FD presets of a palette operand (DA4ACC).
PALETTE_PRESETS = {
    0xFF: ((0x00, 0x01), (0x10, 0x70), (0x90, 0x70)),
    0xFE: ((0x00, 0x01), (0x10, 0x70)),
    0xFD: ((0x90, 0x70),),
}


@dataclass(frozen=True)
class Instruction:
    offset: int
    opcode: int
    size: int
    targets: tuple[int, ...]  # script addresses it may go to, besides the next instruction
    texts: tuple[int, ...]  # text pointers
    data: tuple[tuple[int, int], ...]  # (offset, length) of the room data it reads (palette colours)
    operands: tuple[int | bytes, ...]  # one per operand kind: the value, or a list's bytes with its end

    @property
    def name(self) -> str:
        return opcode_names.get(self.opcode, f"op_{self.opcode:02x}")

    @property
    def falls_through(self) -> bool:
        return self.opcode not in STOPS


class DecodeError(ValueError):
    pass


def palette_bytes(first: int, count: int) -> int:
    """How many colour bytes load_palette (51) reads for its palette operand."""
    ranges = PALETTE_PRESETS.get(first, ((first, count),))
    return 2 * sum(n for _, n in ranges)


def list_length(data: bytes, pos: int, ends: tuple[int, ...]) -> int:
    """Bytes of a list from pos up to and including its terminator."""
    end = pos
    while end < len(data) and data[end] not in ends:
        end += 1
    if end >= len(data):
        raise DecodeError(f"list at {pos:#06x} runs past the room's end")
    return end + 1 - pos


def decode(data: bytes, pos: int) -> Instruction:
    """The instruction at pos; DecodeError for an opcode the VM does not define or one that runs past the data."""
    opcode = data[pos]
    kinds = OPERANDS.get(opcode)
    if kinds is None:
        raise DecodeError(f"opcode {opcode:#04x} at {pos:#06x} is not defined")
    at = pos + 1
    targets: list[int] = []
    texts: list[int] = []
    bytes_read: list[int] = []
    extra: list[tuple[int, int]] = []
    operands: list[int | bytes] = []
    for kind in kinds:
        if kind in LIST_ENDS:
            length = list_length(data, at, LIST_ENDS[kind])
            operands.append(bytes(data[at : at + length]))
            at += length
            continue
        width = WIDTHS[kind]
        if at + width > len(data):
            raise DecodeError(f"opcode {opcode:#04x} at {pos:#06x} runs past the room's end")
        value = int.from_bytes(data[at : at + width], "little")
        if kind == "j":
            targets.append(value)
        elif kind == "t":
            texts.append(value)
        elif kind == "p":
            extra.append((value, palette_bytes(bytes_read[0], bytes_read[1])))
        elif kind == "b":
            bytes_read.append(value)
        operands.append(value)
        at += width
    return Instruction(pos, opcode, at - pos, tuple(targets), tuple(texts), tuple(extra), tuple(operands))


def main(argv: list[str]) -> None:
    for arg in argv:
        opcode = int(arg, 16)
        print(f"{opcode:02X} {opcode_names.get(opcode, '?')}({OPERANDS.get(opcode, '?')})")


if __name__ == "__main__":
    main(sys.argv[1:])
