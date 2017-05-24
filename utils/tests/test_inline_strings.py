import io
from unittest.case import TestCase

from a816.cpu.cpu_65c816 import snes_to_rom
from a816.program import Program

from utils.inline_strings import dragon_find_address


class StubWriter(object):
    def __init__(self):
        self.data = []

    def begin(self):
        pass

    def write_block(self, block, block_address):
        self.data.append(block)

    def end(self):
        pass


class InlineStringTestCase(TestCase):
    def _build_program(self, input_program):
        writer = StubWriter()
        program = Program()

        nodes = program.parser.parse(input_program)
        program.resolve_labels(nodes)
        program.emit(nodes, writer)
        xref = snes_to_rom(program.resolver.current_scope['xref'])
        bytes_io = io.BytesIO(writer.data[0])
        return xref, bytes_io

    def test_dragon_find_address(self):
        xref, bytes_io = self._build_program('''
        *=0x8000
        lda #0x1d
        sta 0x5e
        lda #0xdb 
        sta 0x5f
        lda #0xc1 
        sta 0x60
        xref:
        jsr.w 0x0000
        ''')
        address, byte_addr = dragon_find_address(bytes_io, xref)

        self.assertEqual(0xc1db1d, address)

    def test_dragon_find_address_with_phx(self):
        xref, bytes_io = self._build_program('''
        *=0x8000
        lda #0x1d
        sta 0x5e
        lda #0xdb 
        sta 0x5f
        lda #0xc1 
        sta 0x60
        phx
        xref:
        jsr.w 0x0000
        ''')
        address, byte_addr = dragon_find_address(bytes_io, xref)

        self.assertEqual(0xc1db1d, address)
