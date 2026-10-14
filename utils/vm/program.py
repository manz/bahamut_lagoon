import json
import struct
from collections.abc import Callable
from sys import stdout
from typing import BinaryIO, Literal, TextIO

type Operand = tuple[Literal["byte", "word", "reference"], int] | tuple[Literal["raw"], bytes | bytearray]
type Operands = tuple[Literal["data"], *tuple[Operand, ...]]
type OpcodeElement = tuple[Literal["opcode"], str, int, Operands | None]
type TextElement = tuple[Literal["text"], bytes]
type ReferenceElement = tuple[Literal["reference"], int]
type Element = OpcodeElement | TextElement | ReferenceElement | Operands
type Entry = tuple[Element, str | None, int]
type Listing = dict[int, Entry]


class Program:
    def __init__(self, opcode_names: dict[int, str]) -> None:
        self._program: Listing = {}
        self._labels: set[int] = set()
        self._actors: set[int] = set()
        self._data: dict[int, bytes] = {}
        self._text_pointers: dict[int, set[int]] = {}
        self._opcode_names = opcode_names

    @property
    def actors(self) -> set[int]:
        return self._actors

    def put_opcode(
        self, addr: int, opcode: int, data: Operands | None, comment: str | None = None, *, size: int
    ) -> None:
        if self._program.get(addr) is None:
            opcode_name = self._opcode_names.get(opcode, "__opcode")
            self._put(addr, ("opcode", opcode_name, opcode, data), comment, size)

            # 0x12 show actor
            # if opcode == 0x12:
            #     self._actors.add(data[1][1][0])

    def filter(self, condition: Callable[[int, Entry], bool]) -> Listing:
        retval = {}
        for key in sorted(self._program.keys()):
            element = self._program[key]

            if condition(key, element):
                retval[key] = element
        return retval

    def put_text_data(self, address: int, data: bytes, decoded: str) -> None:
        self._put(address, ("text", data), decoded, len(data))

    def put_data(self, address: int, data: bytes) -> None:
        self._put(address, ("data", ("raw", data)), None, len(data))

    def put_reference(self, address: int, reference: int, comment: str | None = None) -> None:
        self.put_label(reference)
        self._put(address, ("reference", reference), comment, 2)

    def put_text_pointer(self, text_reference: int, pointer: int) -> None:
        if text_reference in self._text_pointers:
            self._text_pointers[text_reference].add(pointer)
        else:
            self._text_pointers[text_reference] = {pointer}

    def _put(self, address: int, data: Element, comment: str | None, size: int) -> None:
        self._program[address] = (data, comment, size)

    def put_label(self, address: int) -> None:
        self._labels.add(address)

    def display_program_part(self, out: TextIO, program: Listing) -> None:
        def format_data(data: Operands | Operand | None) -> str:
            if data:
                retval = []
                if data[0] == "data":
                    for d in data[1:]:
                        retval.append(format_data(d))
                    return ", ".join(retval)
                else:
                    if data[0] == "byte":
                        return f"{data[1]:#02x}"
                    elif data[0] == "word":
                        return f"{data[1]:#04x}"
                    elif data[0] == "reference":
                        return f"ref(__{data[1]:#04x})"
                    elif data[0] == "raw":
                        return ",".join([f"{i:#02x}" for i in data[1]])
            else:
                return ""

        def format_opcode(opcode_tuple: OpcodeElement) -> str:
            _, name, opcode, data = opcode_tuple
            return f"{opcode:#02x} {name}({format_data(data)})"

        def format_element(element: Element) -> str:
            if element[0] == "opcode":
                return format_opcode(element)
            elif element[0] == "reference":
                return f"reference({element[1]:#02x})"
            elif element[0] == "text":
                return "text"
            else:
                return str(element)

        for key in sorted(program.keys()):
            if key in self._labels:
                out.write(f"__0x{key:02x}:\n")
            element = format_element(program[key][0])
            raw_comment = program[key][1]
            comment = raw_comment.replace("\n", " ") if raw_comment else None

            if comment:
                comment = comment.replace("\\s", " ")
                out.write(f"{key:#04x} : {element: <80} # {comment}\n")
            else:
                out.write(f"{key:#04x} : {element}\n")

    def display_program(self, out: TextIO | None = None) -> None:
        out = out or stdout

        self.display_program_part(out, self._program)

    def dump_as_json(self, out: TextIO | None = None) -> None:
        out = out or stdout

        class BytesEncoder(json.JSONEncoder):
            def default(self, obj: object) -> object:
                if isinstance(obj, (bytearray, bytes)):
                    return obj.decode("unicode-escape")
                return json.JSONEncoder.default(self, obj)

        out.write(json.dumps(self._program, cls=BytesEncoder))

    def compile(self, output_file: str) -> None:
        def serialize_data(output: BinaryIO, data: Operands | Operand | None) -> None:
            if data:
                if data[0] == "data":
                    for d in data[1:]:
                        serialize_data(output, d)
                elif data[0] == "byte":
                    output.write(struct.pack("B", data[1]))
                elif data[0] == "word" or data[0] == "reference":
                    output.write(struct.pack("<H", data[1]))
                elif data[0] == "raw":
                    output.write(data[1])

        with open(output_file, "wb") as output:
            for address in sorted(self._program.keys()):
                output.seek(address)

                data, _comment, _size = self._program[address]

                if data[0] == "reference":
                    output.write(struct.pack("<H", data[1]))
                elif data[0] == "data":
                    serialize_data(output, data)
                elif data[0] == "opcode":
                    output.write(struct.pack("B", data[2]))
                    serialize_data(output, data[3])
                elif data[0] == "text":
                    output.write(data[1])

    def opcode_frequency(self) -> None:
        frequency: dict[int, int] = {}
        for address in sorted(self._program.keys()):
            data, _comment, _size = self._program[address]

            if data[0] == "opcode":
                if data[2] in frequency:
                    frequency[data[2]] += 1
                else:
                    frequency[data[2]] = 1

        sorted_items = sorted(frequency.items(), key=lambda e: e[1])

        for opcode, freq in sorted_items:
            print("{opcode:#04x} : {freq}")

    def check_for_gaps(self) -> None:
        """Never worked that well"""
        start = 0
        end = 0
        keys = iter(sorted(self._program.keys()))

        for address in keys:
            next_address = next(keys)
            if next_address:
                _, _, size = self._program[address]
                tmp = address + size

                if tmp != next_address:
                    print("slice", hex(start), hex(end))
                    start = next_address
                    end = next_address
                else:
                    end = next_address
        print("end slice", hex(start), hex(end))
