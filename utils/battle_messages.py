"""
The battle engine's messages that its code points at directly, in bank C0 (C0ECEA-C0EFEE): unit info, map titles,
drowning, saving, damage, experience, items.

Each <string> of text/battle_messages.xml names its vanilla address (address), the instructions that load it
(refs: an ldx or ldy, the operand after the opcode), and how its loader sizes the copy:

- count: the lda #n before C0A113 / C0A116, which copy exactly n bytes into the battle line. A "prefix" string is
  followed by more text in the line (n is its length); a "line" string ends with its FF (n counts it). Strings
  sharing a count site take the largest.
- digits: the ldx #$06xx after it that places a number at the line position the string ends at.
- digit: the sta $07xx that writes a digit over the string's "#".

The others end at their FF. The strings move to the inline strings' bank; insert_battle_messages patches the loaders'
banks (BANK_SITES), the references and the counts. Strings with font="small" are drawn by the battle panel, the rest
by the battle dialogue font.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from script import Table

from utils.cartridge import rom_address, rom_offset
from utils.name_tables import encode

MESSAGES = Path("text/battle_messages.xml")
END = 0xFF
LINE = 0x0620  # the battle line, seen through D = 0x100 by its number writers
LINE_BUS = 0x0720  # the battle line, as C0A113 addresses it
DIGIT = "#"  # stands for the digit the engine writes into the line
SMALL_FONT_COLON = "[0x30]"

# The bank operand of every loader: C0A113's copy, C0A942's, C0A9B8's caller and the two panel copy groups.
BANK_SITES = (0xC0A11B, 0xC0A945, 0xC0355F, 0xC0DB85, 0xC0DBA8)


@dataclass(frozen=True)
class BattleMessage:
    text: str
    refs: tuple[int, ...]
    count: int | None = None
    kind: str = "line"
    digits: int | None = None
    digit: int | None = None
    small: bool = False


def read_messages(source: Path = MESSAGES) -> list[BattleMessage]:
    def address(value: str | None) -> int | None:
        return int(value, 16) if value else None

    messages = []
    for string in ET.parse(source).getroot():
        messages.append(
            BattleMessage(
                text=string.text or "",
                refs=tuple(int(ref, 16) for ref in (string.get("refs") or "").split()),
                count=address(string.get("count")),
                kind=string.get("kind", "line"),
                digits=address(string.get("digits")),
                digit=address(string.get("digit")),
                small=string.get("font") == "small",
            )
        )
    return messages


def encode_message(table: Table, message: BattleMessage) -> bytes:
    """The message's codes, FF-terminated; the panel's small font folds accented capitals and takes its colon."""
    text = message.text.replace(DIGIT, "0")
    if message.small:
        return encode(table, text.replace(":", SMALL_FONT_COLON)) + bytes([END])
    return table.to_bytes(text.replace(" ", r"\s")) + bytes([END])


def copy_count(message: BattleMessage, codes: bytes) -> int:
    """The bytes C0A113 copies: the text alone before more text, the text and its FF for a whole line."""
    return len(codes) - 1 if message.kind == "prefix" else len(codes)


def patches(table: Table, messages: list[BattleMessage], address: int) -> tuple[bytes, dict[int, bytes]]:
    """The strings laid out from bus address `address`, and the code patches: ROM bus address -> bytes."""
    data = b""
    code: dict[int, bytes] = {site: bytes([address >> 16]) for site in BANK_SITES}
    counts: dict[int, int] = {}
    for message in messages:
        codes = encode_message(table, message)
        pointer = (address + len(data)) & 0xFFFF
        for ref in message.refs:
            code[ref + 1] = pointer.to_bytes(2, "little")
        if message.count is not None:
            counts[message.count] = max(counts.get(message.count, 0), copy_count(message, codes))
        if message.digits is not None:
            code[message.digits + 1] = (LINE + len(codes) - 1).to_bytes(2, "little")
        if message.digit is not None:
            code[message.digit + 1] = (LINE_BUS + message.text.index(DIGIT)).to_bytes(2, "little")
        data += codes
    for site, count in counts.items():
        code[site + 1] = bytes([count])
    return data, code


def insert_battle_messages(writer, offset: int) -> int:
    """Write the messages at ROM offset `offset` and patch their loaders; return the bus address past them."""
    table = Table("./text/table/mz.tbl")
    address = rom_address(offset)
    data, code = patches(table, read_messages(), address)
    if (address + len(data) - 1) >> 16 != address >> 16:
        raise ValueError("the battle messages must stay in one bank: their loaders take a single bank")
    writer.write_block(data, offset)
    for site, block in code.items():
        writer.write_block(block, rom_offset(site))
    return address + len(data)
