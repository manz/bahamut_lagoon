import io
from unittest.case import TestCase

from a816.program import Program
from script import Table

from utils.cartridge import rom_address
from utils.inline_strings import INLINE_CELL, INLINE_RIGHT, dragon_find_address, inline_record

TABLE = Table("text/table/mz.tbl")


class StubWriter:
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

        error, nodes = program.parser.parse(input_program)
        self.assertIsNone(error)
        program.resolve_labels(nodes)
        program.emit(nodes, writer)
        # the block assembled at 0x8000 stands for ROM offset 0
        xref = rom_address(program.resolver.current_scope["xref"] - 0x8000)
        bytes_io = io.BytesIO(writer.data[0])
        return xref, bytes_io

    def test_dragon_find_address(self):
        xref, bytes_io = self._build_program(
            """
        *=0x8000
        lda #0x1d
        sta 0x5e
        lda #0xdb 
        sta 0x5f
        lda #0xc1 
        sta 0x60
        xref:
        jsr.w 0x0000
        """
        )
        address, _byte_addr = dragon_find_address(bytes_io, xref)

        self.assertEqual(0xC1DB1D, address)

    def test_dragon_find_address_with_phx(self):
        xref, bytes_io = self._build_program(
            """
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
        """
        )
        address, _byte_addr = dragon_find_address(bytes_io, xref)

        self.assertEqual(0xC1DB1D, address)


class InlineRecordTestCase(TestCase):
    def test_a_label_is_its_width_then_one_segment(self):
        self.assertEqual(inline_record(TABLE, "NV"), bytes([2, 0, *TABLE.to_bytes("NV"), 0xFF, 0xFF]))

    def test_padding_is_not_stored(self):
        self.assertEqual(inline_record(TABLE, "Atk.", 8), bytes([8, 0, *TABLE.to_bytes("Atk."), 0xFF, 0xFF]))

    def test_one_space_stays_in_its_segment(self):
        self.assertEqual(inline_record(TABLE, "Coût MP")[1:3], bytes([0, *TABLE.to_bytes("C")]))

    def test_runs_of_spaces_place_segments(self):
        record = inline_record(TABLE, "TEMPS   :  :", 14)
        colon = 0x30  # small_font's
        self.assertEqual(record[-7:], bytes([INLINE_CELL | 8, colon, 0xFF, INLINE_CELL | 11, colon, 0xFF, 0xFF]))

    def test_leading_spaces_start_the_segment_later(self):
        self.assertEqual(inline_record(TABLE, "  ..")[1], 2)

    def test_one_character_is_a_font_cell(self):
        self.assertEqual(inline_record(TABLE, "/")[1], INLINE_CELL)

    def test_right_aligned_segment(self):
        self.assertEqual(inline_record(TABLE, "Tour", 9, "right")[:2], bytes([9, INLINE_RIGHT]))
