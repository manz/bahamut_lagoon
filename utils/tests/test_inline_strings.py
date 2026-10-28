import io
import os
from unittest import mock
from unittest.case import TestCase

from a816.snippet import assemble_source
from katsuji.script import Table

from utils.cartridge import rom_address
from utils.inline_strings import (
    INLINE_CELL,
    INLINE_RIGHT,
    InlineStringHook,
    dragon_find_address,
    inline_record,
    inline_string_hooks_source,
    release_version,
)

TABLE = Table("text/table/mz.tbl")


class InlineStringTestCase(TestCase):
    def _build_program(self, input_program: str) -> tuple[int, io.BytesIO]:
        assembled = assemble_source(input_program)
        # the block assembled at 0x8000 stands for ROM offset 0
        xref = rom_address(int(assembled.symbols["xref"]) - 0x8000)
        return xref, io.BytesIO(assembled.blocks[0][1])

    def test_dragon_find_address(self) -> None:
        xref, bytes_io = self._build_program(
            """
        .alloc at 0x8000 {
        lda #0x1d
        sta 0x5e
        lda #0xdb
        sta 0x5f
        lda #0xc1
        sta 0x60
        xref:
        jsr.w 0x0000
        }
        """
        )
        address, _byte_addr = dragon_find_address(bytes_io, xref)

        self.assertEqual(0xC1DB1D, address)

    def test_dragon_find_address_with_phx(self) -> None:
        xref, bytes_io = self._build_program(
            """
        .alloc at 0x8000 {
        lda #0x1d
        sta 0x5e
        lda #0xdb
        sta 0x5f
        lda #0xc1
        sta 0x60
        phx
        xref:
        jsr.w 0x0000
        }
        """
        )
        address, _byte_addr = dragon_find_address(bytes_io, xref)

        self.assertEqual(0xC1DB1D, address)


def record(text: str, width: int | None = None, align: str | None = None, ids: dict[bytes, int] | None = None) -> bytes:
    return inline_record(TABLE, text, {} if ids is None else ids, width, align)


class InlineRecordTestCase(TestCase):
    def test_a_label_is_its_width_then_one_segment(self) -> None:
        self.assertEqual(record("NV"), bytes([2, 0, *TABLE.to_bytes("NV"), 0xFF, 0, 0, 0xFF]))

    def test_padding_is_not_stored(self) -> None:
        self.assertEqual(record("Atk.", 8), bytes([8, 0, *TABLE.to_bytes("Atk."), 0xFF, 0, 0, 0xFF]))

    def test_one_space_stays_in_its_segment(self) -> None:
        self.assertEqual(record("Coût MP")[1:3], bytes([0, *TABLE.to_bytes("C")]))

    def test_runs_of_spaces_place_segments(self) -> None:
        colon = 0x30  # small_font's
        self.assertEqual(
            record("TEMPS   :  :", 14)[-11:],
            bytes([INLINE_CELL | 8, colon, 0xFF, 1, 0, INLINE_CELL | 11, colon, 0xFF, 1, 0, 0xFF]),
        )

    def test_leading_spaces_start_the_segment_later(self) -> None:
        self.assertEqual(record("  ..")[1], 2)

    def test_one_character_is_a_font_cell(self) -> None:
        self.assertEqual(record("/")[1], INLINE_CELL)

    def test_right_aligned_segment(self) -> None:
        self.assertEqual(record("Tour", 9, "right")[:2], bytes([9, INLINE_RIGHT]))

    def test_identical_segments_share_an_id(self) -> None:
        ids: dict[bytes, int] = {}
        record("NV", ids=ids)
        self.assertEqual(record("Atk.  NV", 8, ids=ids)[-3:-1], bytes([0, 0]))
        self.assertEqual(list(ids), [TABLE.to_bytes("NV"), TABLE.to_bytes("Atk.")])


class InlineStringHooksTestCase(TestCase):
    def test_a_hook_draws_the_record_then_pads_to_the_return(self) -> None:
        source = inline_string_hooks_source([InlineStringHook(0xEED3D2, 0x02A5, 2)])
        self.assertIn(
            ".alloc at 0xEED3D2 {\n    jsr.w draw_inline_string_patched\n    .dw 0x02A5\n    nop\n    nop\n}", source
        )

    def test_a_hook_with_a_cursor_sets_it_first(self) -> None:
        source = inline_string_hooks_source([InlineStringHook(0xEED3D7, 0x02B9, 3, 0x0068)])
        self.assertIn(
            "    lda.w #0x0068\n    jsr.w 0x495B  ; set_text_cursor\n    jsr.w draw_inline_string_patched", source
        )


class ReleaseVersionTestCase(TestCase):
    def test_the_release_tag_is_the_version(self) -> None:
        with mock.patch.dict(os.environ, {"BL_VERSION": "v1.0.0a0"}):
            self.assertEqual(release_version(), "v1.0.0a0")

    def test_a_local_build_is_dev(self) -> None:
        with mock.patch.dict(os.environ, {"BL_VERSION": ""}):
            self.assertEqual(release_version(), "dev")
