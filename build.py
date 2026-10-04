#!/usr/bin/env python3
import argparse
import logging
import os
import struct
from pathlib import Path

from a816.module_builder import build_with_imports
from a816.writers import IPSWriter, Writer
from script import Table

from utils.cartridge import rom_address, rom_offset
from utils.decompress_gfx import compress_asset, lz_compress_gfx
from utils.dump_battle_rooms import build_battle_text_patch
from utils.dump_rooms import build_text_patch
from utils.inline_strings import (
    insert_battle_commands_strings,
    insert_battle_fixed,
    insert_char_names,
    insert_dragon_feed_inline_strings,
    insert_inline_strings,
    insert_messages_strings,
)


class Context:
    table: Table


logger = logging.getLogger(__name__)


CODE_IPS = Path("build/code.ips")


def build_code(source: str) -> dict[str, int]:
    """Assemble the a816 sources into CODE_IPS and return their symbols."""
    obj_dir = Path("build/obj")
    if obj_dir.exists():
        for o in obj_dir.glob("*.o"):
            o.unlink()
    CODE_IPS.unlink(missing_ok=True)

    result = build_with_imports(
        main_source=Path(source),
        output_file=CODE_IPS,
        output_format="ips",
        output_dir=obj_dir,
        overlap_mode="warn",
    )
    if result.exit_code != 0:
        raise SystemExit("\n".join(result.diagnostics) or "a816 build failed")
    if not CODE_IPS.exists():
        raise SystemExit(f"a816 reported success but {CODE_IPS} was not produced")
    return result.symbol_map


def ips_records(path: Path) -> bytes:
    """The records of an IPS file, without its PATCH header and EOF trailer."""
    data = path.read_bytes()
    if not (data.startswith(b"PATCH") and data.endswith(b"EOF")):
        raise ValueError(f"{path} is not an IPS patch")
    return data[5:-3]


class DebugWriter(IPSWriter):
    def write_block_header(self, block: bytes, block_address: int) -> None:
        super().write_block_header(block, block_address)
        print(
            f"DEBUGIPS: {rom_address(block_address):#x} {len(block):#x}"
        )


def build_rooms_partials(writer: Writer, table: Table) -> None:
    with open("bl.sfc", "rb") as rom:
        address = build_text_patch(rom, table, writer, rom_offset(0xF00000))
        print(f"Relocated dialog rooms end at {address + 0xC00000:#0x}")

        address = build_battle_text_patch(rom, table, writer, address)
        print(f"Relocated battle rooms end at {address + 0xC00000:#0x}")


partials_builder = {"rooms": build_rooms_partials}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build patch.")

    parser.add_argument(
        "--debug", dest="debug", action="store_true", help="Turns debug on"
    )

    parser.add_argument("--rooms", action="store_true", help="build rooms partial")

    args = parser.parse_args()

    lang = "mz"
    table_path = os.path.join(os.path.dirname(__file__), "text/table")
    table = Table(os.path.join(table_path, f"{lang}.tbl"))

    if args.rooms:
        with open("rooms.partial", "wb") as partial:
            writer = IPSWriter(partial)
            build_rooms_partials(writer, table)
    else:
        with open("bl.ips", "wb") as f:
            writer = IPSWriter(f)
            writer.begin()

            if os.path.exists("rooms.partial"):
                with open("rooms.partial", "rb") as partial:
                    f.write(partial.read())
            else:
                build_rooms_partials(writer, table)

            symbols = build_code("bl.s")
            f.write(ips_records(CODE_IPS))
            # get address for draw_inline_string_patched for code generation.
            draw_inline_string_ref = symbols["draw_inline_string_patched"]

            insert_dragon_feed_inline_strings(writer, rom_offset(0xFC0000))
            end_of_battle_commands = insert_battle_commands_strings(
                writer, rom_offset(0xFD0000)
            )
            end_of_inline_strings = insert_inline_strings(
                writer, rom_offset(end_of_battle_commands + 1), draw_inline_string_ref
            )

            end_of_message_strings = insert_messages_strings(
                writer, rom_offset(end_of_inline_strings + 1)
            )

            def insert_compressed_asset(
                writer, asset_filename, insert_addr, low_addr, bank_addr, compressor
            ):
                with open(asset_filename, "rb") as asset:
                    data = asset.read()
                    compressed = compressor(data)
                    writer.write_block(compressed, rom_offset(insert_addr + 1))
                    # .D5:E6B9                 LDA     #$9A4F
                    # .D5:E6BC                 STA     D, $28
                    # .D5:E6BE                 SEP     #$20 ; ' '
                    # .D5:E6C0 .A8
                    # .D5:E6C0                 LDA     #$E8 ; 'Þ'
                    writer.write_block(
                        struct.pack("<H", insert_addr + 1 & 0xFFFF),
                        rom_offset(low_addr),
                    )
                    writer.write_block(
                        struct.pack("B", (insert_addr + 1) >> 16),
                        rom_offset(bank_addr),
                    )

                    return rom_address(rom_offset(insert_addr) + 1 + len(compressed))

            next_insert = insert_compressed_asset(
                writer,
                "src_assets/e89a4f.bin",
                insert_addr=end_of_message_strings,
                low_addr=0xD5E6B9 + 1,
                bank_addr=0xD5E6C0 + 1,
                compressor=lz_compress_gfx,
            )
            # .EE:850F                 .WORD $20
            # .EE:8511                 .BYTE $EE
            insert_compressed_asset(
                writer,
                "src_assets/ee0020.bin",
                insert_addr=next_insert,
                low_addr=0xEE850F,
                bank_addr=0xEE8511,
                compressor=compress_asset,
            )
            # too much ? maybe
            # with open('src_assets/e89a4f.bin', 'rb') as asset:
            #     data = asset.read()
            #     compressed = lz_compress_gfx(data)
            #     writer.write_block(compressed, rom_offset(end_of_message_strings + 1))
            #
            # # .D5:E6B9                 LDA     #$9A4F
            # # .D5:E6BC                 STA     D, $28
            # # .D5:E6BE                 SEP     #$20 ; ' '
            # # .D5:E6C0 .A8
            # # .D5:E6C0                 LDA     #$E8 ; 'Þ'
            # writer.write_block(struct.pack('<H', end_of_message_strings + 1 & 0xFFFF), rom_offset(0xD5E6B9 + 1))
            # writer.write_block(struct.pack('B', (end_of_message_strings + 1) >> 16), rom_offset(0xD5E6C0 + 1))

            insert_char_names(writer)
            insert_battle_fixed(writer)

            writer.end()
