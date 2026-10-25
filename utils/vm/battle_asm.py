"""Encoder for the battle scripts utils.vm.battle_script decodes: the same instructions back to bytes, exactly (every
room re-encodes to its own script), and a small assembler with labels to write scripts from Python.

    code, labels = assemble([
        op("say", "hello"),
        "loop",
        op("wait", 1),
        op("jump", "loop"),
        "hello",
        b"...\\xff",
    ], base=0x20)

Addresses (j, t operands, labels) are script offsets, like the header words: `base` is where the code lands.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from utils.vm.battle_script import ENTRIES, OPS, Data, Disassembly, Header, Instruction, kinds, size

NAMES = {name: op for op, (name, _) in OPS.items()}


@dataclass(frozen=True)
class Op:
    """An instruction to assemble: a j / t operand may be a label."""

    op: int
    args: tuple[int | str, ...]


def op(name: str, *args: int | str) -> Op:
    code = NAMES[name]
    if len(args) != len(kinds(code)):
        raise ValueError(f"{name} takes {len(kinds(code))} operands, got {len(args)}")
    for kind, arg in zip(kinds(code), args, strict=True):
        if isinstance(arg, str) and kind not in "jt":
            raise TypeError(f"{name}: a {kind} operand cannot be the label {arg!r}")
    return Op(code, args)


def encode(ins: Instruction | Op | Data, labels: dict[str, int] | None = None) -> bytes:
    if isinstance(ins, Data):
        return ins.raw
    out = bytearray([ins.op])
    for kind, arg in zip(kinds(ins.op), ins.args, strict=True):
        value = (labels or {})[arg] if isinstance(arg, str) else arg
        width = 2 if kind in "wjt" else 1
        if not 0 <= value < 1 << 8 * width:
            raise ValueError(f"{ins.op:02x}: operand {value:#x} takes {width} byte(s)")
        out += value.to_bytes(width, "little")
    return bytes(out)


def encode_header(head: Header) -> bytes:
    words = (*head.entries, head.area_table, head.text_table)
    if len(head.entries) != ENTRIES:
        raise ValueError(f"a header has {ENTRIES} entries")
    return b"".join(w.to_bytes(2, "little") for w in words)


def encode_script(dis: Disassembly) -> bytes:
    return encode_header(dis.header) + b"".join(encode(item) for _, item in dis.items)


def _length(item: Instruction | Op | Data | bytes) -> int:
    if isinstance(item, bytes):
        return len(item)
    return len(item.raw) if isinstance(item, Data) else size(item.op)


def assemble(items: Sequence[str | Op | Instruction | Data | bytes], base: int) -> tuple[bytes, dict[str, int]]:
    """Strings are labels, bytes raw data (a text), the rest instructions; the first lands at script offset `base`.
    Returns the bytes and each label's offset."""
    labels: dict[str, int] = {}
    at = base
    for item in items:
        if isinstance(item, str):
            if item in labels:
                raise ValueError(f"label {item!r} defined twice")
            labels[item] = at
        else:
            at += _length(item)
    out = b"".join(
        item if isinstance(item, bytes) else encode(item, labels) for item in items if not isinstance(item, str)
    )
    return out, labels
