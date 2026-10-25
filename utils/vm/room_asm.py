"""Encoder for the dialog room instructions utils.vm.room_ops decodes: the operands back to bytes, exactly (every
room re-encodes to its own bytes), and a small assembler with labels to write scripts from Python.

    code, labels = assemble([
        op("set_room_bits", 0x02),
        "loop",
        op("wait_frames", 1),
        op("jump_if_flag", 0x10, "loop"),
        op("display_text", "hello"),
        op("exit"),
        "hello",
        b"\\x20\\x21\\xff",
    ], base=0x1400)

Addresses (jump, text and data operands) are offsets from the room's start, as the VM reads them: `base` is where
the code sits in the room. A label operand is a string; plain ints go in as they are.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from utils.vm.opcodes_map import opcode_names
from utils.vm.room_ops import LIST_ENDS, OPERANDS, WIDTHS, Instruction

OPCODES = {name: opcode for opcode, name in opcode_names.items()}
ADDRESS_KINDS = frozenset("jtp")

Operand = int | str | bytes  # a value, a label (address kinds), or a list's bytes


@dataclass(frozen=True)
class Op:
    """An instruction to assemble: its opcode and operands, labels unresolved."""

    opcode: int
    operands: tuple[Operand, ...]


def _encode_list(kind: str, value: Operand) -> bytes:
    if not isinstance(value, bytes):
        raise TypeError(f"a list operand takes bytes, got {value!r}")
    if not value or value[-1] not in LIST_ENDS[kind]:
        raise ValueError(f"list {value.hex(' ')} lacks its end ({', '.join(f'{e:02X}' for e in LIST_ENDS[kind])})")
    return value


def _encode_operand(kind: str, value: Operand, labels: dict[str, int]) -> bytes:
    if kind in LIST_ENDS:
        return _encode_list(kind, value)
    if isinstance(value, str):
        if kind not in ADDRESS_KINDS:
            raise TypeError(f"operand kind {kind!r} cannot take the label {value!r}")
        value = labels[value]
    if not isinstance(value, int):
        raise TypeError(f"operand kind {kind!r} takes a number, got {value!r}")
    return value.to_bytes(WIDTHS[kind], "little")


def encode(ins: Instruction | Op, labels: dict[str, int] | None = None) -> bytes:
    """One instruction's bytes: the opcode, then each operand at its width (lists as they are, end included)."""
    kinds = OPERANDS[ins.opcode]
    if len(ins.operands) != len(kinds):
        raise ValueError(f"{opcode_names[ins.opcode]} takes {len(kinds)} operands, got {len(ins.operands)}")
    body = b"".join(_encode_operand(k, v, labels or {}) for k, v in zip(kinds, ins.operands, strict=True))
    return bytes([ins.opcode]) + body


def _size(item: Op | bytes) -> int:
    if isinstance(item, bytes):
        return len(item)
    return len(encode(item, dict.fromkeys((v for v in item.operands if isinstance(v, str)), 0)))


def assemble(items: Sequence[str | Op | bytes], base: int) -> tuple[bytes, dict[str, int]]:
    """Strings are labels, bytes are data (texts, palettes) and the rest instructions, laid out from offset `base`.
    Returns the bytes and each label's offset in the room."""
    labels: dict[str, int] = {}
    at = base
    for item in items:
        if isinstance(item, str):
            labels[item] = at
        else:
            at += _size(item)
    code = b"".join(
        item if isinstance(item, bytes) else encode(item, labels) for item in items if not isinstance(item, str)
    )
    return code, labels


def op(name: str, *operands: Operand | Sequence[int]) -> Op:
    """`op("actor_move", 1, [0x13, 0x22])`: a list operand takes its steps (or actors) and gets its FF end."""
    opcode = OPCODES[name]
    kinds = OPERANDS[opcode]
    if len(operands) != len(kinds):
        raise ValueError(f"{name} takes {len(kinds)} operands, got {len(operands)}")
    return Op(opcode, tuple(_build(kind, value) for kind, value in zip(kinds, operands, strict=True)))


def _build(kind: str, value: Operand | Sequence[int]) -> Operand:
    if kind in LIST_ENDS and not isinstance(value, (int, str)):
        items = bytes(value)
        return items if items and items[-1] in LIST_ENDS[kind] else items + b"\xff"
    if isinstance(value, (int, str, bytes)):
        return value
    raise TypeError(f"operand kind {kind!r} cannot take {value!r}")
