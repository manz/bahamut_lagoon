from typing import Protocol, Optional

from script import Table

from . import AlreadyVisitedError
from .executor import walk_event_chain
from .room import Room


def bl_prefix_lookup_chars(data_string: bytes) -> bytes:
    current_prefix = 0xF0
    retval = []
    for k in data_string:
        if k in (0xF0, 0xF1, 0xF2, 0xF3):
            current_prefix = k
            continue
        if k != 0xFF:
            retval.append(current_prefix)
        retval.append(k)
    return bytes(retval)


def get_string_from_room(room: Room, address: int, table: Table):
    pos = address
    room_data = room.room
    while True:
        if pos >= len(room_data):
            pos = len(room_data)
            break
        if room_data[pos : pos + 2] in (b"\xff\xff", b"\xfd\xff"):
            pos += 2
            break
        elif room_data[pos] in (0xFF, 0xFD):
            pos += 1
            break
        pos += 1

    # FIXME: does not really work
    if room.lang == "jp":
        text_data = bl_prefix_lookup_chars(bytes(room_data[address:pos]))
    else:
        text_data = bytes(room_data[address:pos])

    decoded_text = table.to_text(text_data)

    room.program.put_text_data(address, text_data, decoded_text.replace("\\s", " "))

    return pos - address, decoded_text


def decode_actor_motion(data):
    motions = {
        0x00: "up",
        0x10: "down",
        0x20: "left",
        0x30: "right",
        0x40: "up-left",
        0x50: "down-right",
        0x60: "down-left",
        0x70: "up-right",
        0x80: "?",
        0x90: "?",
        0xA0: "?",
        0xB0: "?",
        0xC0: "?",
        0xD0: "?",
        0xE0: "?",
        0xF0: "pause?",
    }
    actor_motion = f"actor({data[0]:#02x}): "

    decoded_motions = []

    for d in data[1:-1]:
        motion = d & 0xF0
        quantity = d & 0x0F
        motion_name = motions.get(motion, "unknown_" + hex(motion))
        decoded_motions.append(f"{motion_name}({quantity:#02x})")

    return actor_motion + ", ".join(decoded_motions)


class OpcodeProtocol(Protocol):
    def apply(self, room: Room) -> int:
        """Opcode func"""


class CommentLambda(Protocol):
    def __call__(self, room: Room) -> str: ...


class DataLambda(Protocol):
    def __call__(self, room: Room) -> bytes: ...


class Opcode:
    def __init__(
        self, size: int, data_lambda: Optional[DataLambda] = None, comment_lambda: Optional[CommentLambda] = None
    ) -> None:
        self.size = size
        self.data_lambda = data_lambda
        self.comment_lambda = comment_lambda

    def apply(self, room: Room) -> int:
        if self.data_lambda:
            data = self.data_lambda(room)
        else:
            data = room.get_data(1, self.size)

        if self.comment_lambda:
            comment = self.comment_lambda(room)
        else:
            comment = None

        room.program.put_opcode(room.pc, room.get_byte(), ("data", ("raw", data)), size=self.size, comment=comment)

        return self.size


class StateOpcode:
    def apply(self, room: Room) -> int:
        def decode_bit_op(byte: int) -> str:
            convert_table = [
                0x0001,
                0x0002,
                0x0004,
                0x0008,
                0x0010,
                0x0020,
                0x0040,
                0x0080,
                0x0100,
                0x0200,
                0x0400,
                0x0800,
                0x1000,
                0x2000,
                0x4000,
                0x8000,
            ]
            index = byte >> 3
            value = convert_table[byte & 7]
            return "var: 0x%02x: value %s" % (index, bin(value))

        room.program.put_opcode(
            room.pc,
            room.get_byte(),
            ("data", ("byte", room.get_byte(1))),
            size=2,
            comment=decode_bit_op(room.get_byte(1)),
        )
        return 2


class Opcode13:
    def apply(self, room: Room) -> int:
        i = 1
        b = room.get_byte(i)
        data = [b]
        while b not in (0xFE, 0xFF):
            i += 1
            b = room.get_byte(i)
            data.append(b)

        room.program.put_opcode(
            room.pc,
            room.get_byte(),
            ("data", ("raw", room.get_data(1, len(data) + 1))),
            size=len(data) + 1,
            comment=decode_actor_motion(data),
        )

        return i + 1


class Opcode18:
    def apply(self, room: Room) -> int:
        i = 2
        data = [room.get_byte(1)]
        while room.get_byte(i) != 0xFF:
            data.append(room.get_byte(i))
            i += 1
        data.append(0xFF)
        room.program.put_opcode(
            room.pc, room.get_byte(), ("data", ("raw", room.get_data(1, len(data) + 1))), size=i + 1
        )
        return i + 1


class TextOpcode:
    def __init__(self, size: Optional[int] = 3) -> None:
        self.size = size

    def apply(self, room: Room) -> int:
        text_addr = room.get_word(1)

        bytes_len, text = get_string_from_room(room, text_addr, room.table)
        room.program.put_opcode(room.pc, room.get_byte(), ("data", ("reference", text_addr)), text, size=3)

        room.put_text_reference(room.pc + 1, text_addr, text)

        return self.size


class YesNoChoiceOpcode:
    def apply(self, room: Room) -> int:
        text_addr = room.get_word(1)

        bytes_len, text = get_string_from_room(room, text_addr, room.table)
        room.put_text_reference(room.pc + 1, text_addr, text)
        room.program.put_opcode(
            room.pc,
            room.get_byte(),
            ("data", ("reference", room.get_word(1)), ("reference", room.get_word(3)), ("word", room.get_word(5))),
            text,
            size=7,
        )

        room.save_pc()

        try:
            room.jump_to(room.get_word(3))
            walk_event_chain(room)
        except AlreadyVisitedError:
            pass
        room.restore_pc()

        room.save_pc()
        try:
            room.jump_to(room.get_word(5))
            walk_event_chain(room)
        except AlreadyVisitedError:
            pass
        room.restore_pc()

        return 7


class MultipleChoiceTextOpcode:
    @staticmethod
    def _extract_choice(room: Room, original_pc: int, delta: int):
        room.pc = original_pc
        room.save_pc()
        try:
            room.jump_to(room.get_word(delta))
            walk_event_chain(room)
        except AlreadyVisitedError:
            pass
        room.restore_pc()

    def apply(self, room: Room) -> int:
        original_pc = room.pc

        multiple_choice_intro_text = get_string_from_room(room, room.get_word(1), room.table)[1]
        room.put_text_reference(room.pc + 1, room.get_word(1), multiple_choice_intro_text)

        room.program.put_opcode(
            room.pc,
            room.get_byte(),
            (
                "data",
                ("reference", room.get_word(1)),
                ("reference", room.get_word(3)),
                ("reference", room.get_word(5)),
                ("reference", room.get_word(7)),
            ),
            comment=multiple_choice_intro_text,
            size=9,
        )

        self._extract_choice(room, original_pc, 3)
        self._extract_choice(room, original_pc, 5)
        self._extract_choice(room, original_pc, 7)

        room.pc = original_pc

        return 9


class Jump(Opcode):
    def __init__(self) -> None:
        super().__init__(3)

    def apply(self, room: Room) -> int:
        address = room.get_word(1)

        room.program.put_opcode(room.pc, room.get_byte(), ("data", ("reference", address)), size=3)

        room.jump_to(address)
        return 0


class ConditionalJump(Jump):
    def apply(self, room: Room) -> int:
        current_pc = room.pc
        condition = room.get_byte(1)

        jump_addr = room.get_word(2)
        room.program.put_opcode(
            current_pc, room.get_byte(), ("data", ("byte", condition), ("reference", jump_addr)), size=4
        )

        room.save_pc()
        try:
            room.jump_to(jump_addr)
            walk_event_chain(room)
        except AlreadyVisitedError:
            pass
        room.restore_pc()

        return 4


class ConditionalJumpToSubRoutine:
    def apply(self, room: Room) -> int:
        room.save_pc()
        jump_addr = room.get_word(2)
        room.program.put_opcode(
            room.pc, room.get_byte(), ("data", ("byte", room.get_byte(1)), ("reference", room.get_word(2))), size=4
        )
        try:
            if jump_addr < len(room.room):
                room.push_addr(room.pc + 4)
                room.jump_to(jump_addr)
                walk_event_chain(room)
            else:
                print("jump outside room ? {}", hex(jump_addr))
        except AlreadyVisitedError:
            room.pop_addr()
        room.restore_pc()
        return 4


class JumpToSubRoutine:
    def apply(self, room: Room) -> int:
        room.save_pc()
        jump_addr = room.get_word(1)
        room.program.put_opcode(room.pc, room.get_byte(), ("data", ("reference", room.get_word(1))), size=3)
        try:
            room.push_addr(room.pc + 3)
            room.jump_to(jump_addr)
            walk_event_chain(room)
        except AlreadyVisitedError:
            room.pop_addr()
        room.restore_pc()
        return 3


class BattleOptionalJump:
    def apply(self, room: Room) -> int:
        jump_addr = room.get_word(1)
        room.program.put_opcode(room.pc, room.get_byte(), ("data", ("reference", jump_addr)), size=4)
        room.save_pc()
        try:
            room.jump_to(jump_addr)
            walk_event_chain(room)
        except AlreadyVisitedError:
            pass
        room.restore_pc()
        return 3


class ReturnFromSubRoutine:
    def apply(self, room: Room) -> int:
        room.program.put_opcode(room.pc, room.get_byte(), None, size=1)
        try:
            room.pc = room.pop_addr()
            return 0
        except IndexError:
            raise AlreadyVisitedError
            #   return 1


class IfElseOpcode:
    def apply(self, room: Room) -> int:
        first = room.get_word(1)
        second = room.get_word(3)
        # print('if_else(%x %x)' % (first, second))
        room.program.put_opcode(room.pc, room.get_byte(), ("data", ("reference", first), ("reference", second)), size=5)
        room.program.put_label(first)
        room.program.put_label(second)
        room.save_pc()
        try:
            room.jump_to(first)
            walk_event_chain(room)
        except AlreadyVisitedError:
            pass
        room.restore_pc()

        room.save_pc()
        try:
            room.jump_to(second)
            walk_event_chain(room)
        except AlreadyVisitedError:
            pass
        room.restore_pc()
        return 5


class NinetySixOpcode:
    def apply(self, room: Room) -> int:
        room.program.put_opcode(
            room.pc,
            room.get_byte(),
            ("data", ("byte", room.get_byte(1)), ("byte", room.get_byte(2)), ("word", room.get_word(3))),
            size=5,
        )
        room.program.put_label(room.get_word(3))

        jump_addr = room.get_word(3)

        room.jump_to(jump_addr)
        return 5
