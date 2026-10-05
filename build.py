#!/usr/bin/env python3
import argparse
import logging
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

from a816.module_builder import build_with_imports
from a816.writers import IPSWriter
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

logger = logging.getLogger(__name__)


ROM = Path("build/bl.sfc")
ROOMS_PARTIAL = Path("build/rooms.partial")
VWF_FONT = Path("assets/vwf.bin")  # incbin'd by bl.s
VWF_FONT_SOURCE = Path("fonts/fft.png")
TABLE = Path("text/table/mz.tbl")


@dataclass(frozen=True)
class Variant:
    """One patch build: the release patch, or the same with the game's debug mode on."""

    stem: str
    debug: bool

    @property
    def ips(self) -> Path:
        return Path(f"build/{self.stem}.ips")

    @property
    def symbols(self) -> Path:
        return Path(f"build/{self.stem}.sym")

    @property
    def code_ips(self) -> Path:
        return Path(f"build/{self.stem}-code.ips")

    @property
    def obj_dir(self) -> Path:
        # One object cache per variant: DEBUG changes what the sources assemble to.
        return Path(f"build/obj/{self.stem}")


RELEASE = Variant("bl", debug=False)
DEBUG = Variant("bl-debug", debug=True)


def build_code(source: str, variant: Variant) -> dict[str, int]:
    """Assemble the a816 sources into the variant's code IPS and return their symbols."""
    variant.code_ips.unlink(missing_ok=True)

    result = build_with_imports(
        main_source=Path(source),
        output_file=variant.code_ips,
        output_format="ips",
        output_dir=variant.obj_dir,
        symbols={"DEBUG": int(variant.debug)},
        overlap_mode="warn",
    )
    if result.exit_code != 0:
        raise SystemExit("\n".join(result.diagnostics) or "a816 build failed")
    if not variant.code_ips.exists():
        raise SystemExit(f"a816 reported success but {variant.code_ips} was not produced")
    if result.program is not None:
        result.program.exports_symbol_file(str(variant.symbols))
    return result.symbol_map


def ips_records(path: Path) -> bytes:
    """The records of an IPS file, without its PATCH header and EOF trailer."""
    data = path.read_bytes()
    if not (data.startswith(b"PATCH") and data.endswith(b"EOF")):
        raise ValueError(f"{path} is not an IPS patch")
    return data[5:-3]


def assets_need_refresh(sources: list[Path], destination: Path) -> bool:
    """Whether destination is missing or older than any of its sources."""
    if not destination.exists():
        return True
    built = destination.stat().st_mtime
    return any(source.stat().st_mtime > built for source in sources)


def build_vwf_font() -> None:
    from utils.font import char_length_override, convert_font

    VWF_FONT.parent.mkdir(exist_ok=True)
    VWF_FONT.write_bytes(convert_font(str(VWF_FONT_SOURCE), empty_chars=char_length_override))


def build_rooms_partial(table: Table) -> None:
    with ROOMS_PARTIAL.open("wb") as partial, ROM.open("rb") as rom:
        writer = IPSWriter(partial)
        address = build_text_patch(rom, table, writer, rom_offset(0xF00000))
        logger.info("Relocated dialog rooms end at %#x", address + 0xC00000)

        address = build_battle_text_patch(rom, table, writer, address)
        logger.info("Relocated battle rooms end at %#x", address + 0xC00000)


def insert_compressed_asset(writer, asset_filename, insert_addr, low_addr, bank_addr, compressor):
    with open(asset_filename, "rb") as asset:
        compressed = compressor(asset.read())
    writer.write_block(compressed, rom_offset(insert_addr + 1))
    # .D5:E6B9                 LDA     #$9A4F
    # .D5:E6BC                 STA     D, $28
    # .D5:E6BE                 SEP     #$20 ; ' '
    # .D5:E6C0 .A8
    # .D5:E6C0                 LDA     #$E8 ; 'Þ'
    writer.write_block(struct.pack("<H", insert_addr + 1 & 0xFFFF), rom_offset(low_addr))
    writer.write_block(struct.pack("B", (insert_addr + 1) >> 16), rom_offset(bank_addr))
    return rom_address(rom_offset(insert_addr) + 1 + len(compressed))


def build_ips(variant: Variant) -> None:
    with variant.ips.open("wb") as f:
        writer = IPSWriter(f)
        writer.begin()
        f.write(ROOMS_PARTIAL.read_bytes())

        symbols = build_code("bl.s", variant)
        f.write(ips_records(variant.code_ips))
        # get address for draw_inline_string_patched for code generation.
        draw_inline_string_ref = symbols["draw_inline_string_patched"]

        insert_dragon_feed_inline_strings(writer, rom_offset(0xFC0000))
        end_of_battle_commands = insert_battle_commands_strings(writer, rom_offset(0xFD0000))
        end_of_inline_strings = insert_inline_strings(
            writer, rom_offset(end_of_battle_commands + 1), draw_inline_string_ref
        )
        end_of_message_strings = insert_messages_strings(writer, rom_offset(end_of_inline_strings + 1))

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

        insert_char_names(writer)
        insert_battle_fixed(writer)

        writer.end()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Bahamut Lagoon patch into build/.")
    parser.add_argument("--debug", action="store_true", help="build build/bl-debug.ips with debug mode on")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="-v for progress, -vv for room dumps")
    args = parser.parse_args()
    level = (logging.WARNING, logging.INFO, logging.DEBUG)[min(args.verbose, 2)]
    logging.basicConfig(level=level, format="%(message)s")

    if not ROM.is_file() or ROM.stat().st_size == 0:
        logger.error("%s missing. Place an unheadered Bahamut Lagoon (J) ROM there.", ROM)
        return 1

    if assets_need_refresh([VWF_FONT_SOURCE], VWF_FONT):
        build_vwf_font()

    room_sources = [TABLE, *Path("text/dialog").glob("*.xml"), *Path("text/battle").glob("*.xml")]
    if assets_need_refresh(room_sources, ROOMS_PARTIAL):
        build_rooms_partial(Table(str(TABLE)))

    build_ips(DEBUG if args.debug else RELEASE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
