#!/usr/bin/env python3
import argparse
import io
import logging
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

from a816.module_builder import build_with_imports
from a816.writers import IPSWriter
from katsuji import build as katsuji_build
from katsuji import config as katsuji_config
from script import Table

from utils.battle_messages import insert_battle_messages
from utils.cartridge import rom_address, rom_offset
from utils.decompress_gfx import compress_asset, lz_compress_gfx
from utils.dump_battle_rooms import build_battle_text_patch
from utils.dump_rooms import build_text_patch
from utils.inline_strings import (
    InlineStringHook,
    inline_string_hooks_source,
    insert_battle_commands_strings,
    insert_dragon_feed_inline_strings,
    insert_inline_strings,
    insert_messages_strings,
)
from utils.name_tables import BAKED_TILES, insert_item_names, insert_short_names, long_names_source
from utils.naming_screen import naming_font_tiles, naming_grids_source
from utils.small_vwf_bake import FONT as SMALL_FONT

logger = logging.getLogger(__name__)


ROM = Path("build/bl.sfc")
ROOMS_PARTIAL = Path("build/rooms.partial")
KATSUJI_CONFIG = Path("katsuji.toml")  # every font: assets/vwf.bin (dialogue) and assets/small_font.dat (8x8)
TABLE = Path("text/table/mz.tbl")
INLINE_STRING_HOOKS = Path("build/gen/inline_string_hooks.s")  # generated module bl.s imports
LONG_NAMES = Path("build/gen/long_names.s")  # generated module small_vwf reads
NAMING_GRIDS = Path("build/gen/naming_grids.s")  # generated module: the naming screen's pages


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


def build_code(source: str, variant: Variant) -> None:
    """Assemble the a816 sources into the variant's code IPS."""
    variant.code_ips.unlink(missing_ok=True)

    result = build_with_imports(
        main_source=Path(source),
        output_file=variant.code_ips,
        output_format="ips",
        output_dir=variant.obj_dir,
        symbols={"DEBUG": int(variant.debug)},
        overlap_mode="error",
    )
    if result.exit_code != 0:
        raise SystemExit("\n".join(result.diagnostics) or "a816 build failed")
    if not variant.code_ips.exists():
        raise SystemExit(f"a816 reported success but {variant.code_ips} was not produced")
    if result.program is not None:
        result.program.exports_symbol_file(str(variant.symbols))


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


def build_rooms_partial(table: Table) -> None:
    with ROOMS_PARTIAL.open("wb") as partial, ROM.open("rb") as rom:
        writer = IPSWriter(partial)
        address = build_text_patch(rom, table, writer, rom_offset(0xF00000))
        logger.info("Relocated dialog rooms end at %#x", address + 0xC00000)

        address = build_battle_text_patch(rom, table, writer, address)
        logger.info("Relocated battle rooms end at %#x", address + 0xC00000)


def insert_compressed_asset(writer, asset, insert_addr, low_addr, bank_addr, compressor):
    """Compress `asset` (a file, or its bytes) into the ROM and point the loader at it."""
    compressed = compressor(asset if isinstance(asset, bytes) else Path(asset).read_bytes())
    writer.write_block(compressed, rom_offset(insert_addr + 1))
    # .D5:E6B9                 LDA     #$9A4F
    # .D5:E6BC                 STA     D, $28
    # .D5:E6BE                 SEP     #$20 ; ' '
    # .D5:E6C0 .A8
    # .D5:E6C0                 LDA     #$E8 ; 'Þ'
    writer.write_block(struct.pack("<H", insert_addr + 1 & 0xFFFF), rom_offset(low_addr))
    writer.write_block(struct.pack("B", (insert_addr + 1) >> 16), rom_offset(bank_addr))
    return rom_address(rom_offset(insert_addr) + 1 + len(compressed))


def insert_text(writer: IPSWriter) -> tuple[list[InlineStringHook], list[bytes]]:
    """Write the relocated strings and graphics; return the inline string call hooks the code must carry and the
    inline segments' codes by baked id."""
    insert_dragon_feed_inline_strings(writer, rom_offset(0xFC0000))
    end_of_battle_commands = insert_battle_commands_strings(writer, rom_offset(0xFD0000))
    end_of_inline_strings, hooks, segments = insert_inline_strings(writer, rom_offset(end_of_battle_commands + 1))
    end_of_message_strings = insert_messages_strings(writer, rom_offset(end_of_inline_strings + 1))
    end_of_battle_messages = insert_battle_messages(writer, rom_offset(end_of_message_strings + 1))

    next_insert = insert_compressed_asset(
        writer,
        "src_assets/e89a4f.bin",
        insert_addr=end_of_battle_messages,
        low_addr=0xD5E6B9 + 1,
        bank_addr=0xD5E6C0 + 1,
        compressor=lz_compress_gfx,
    )
    # .EE:850F                 .WORD $20
    # .EE:8511                 .BYTE $EE
    insert_compressed_asset(
        writer,
        naming_font_tiles(Table(str(TABLE))),  # src_assets/ee0020.bin, its grid glyphs redrawn
        insert_addr=next_insert,
        low_addr=0xEE850F,
        bank_addr=0xEE8511,
        compressor=compress_asset,
    )

    insert_short_names(writer, Table(str(TABLE)))
    insert_item_names(writer, Table(str(TABLE)))
    return hooks, segments


def write_if_changed(path: Path, data: str | bytes) -> None:
    """Leave an unchanged file alone, so a816's object cache stays valid."""
    data = data.encode() if isinstance(data, str) else data
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)


def build_ips(variant: Variant) -> None:
    # The text goes first: its layout decides the inline string pointers the code's call hooks carry.
    text = io.BytesIO()
    hooks, segments = insert_text(IPSWriter(text))
    write_if_changed(INLINE_STRING_HOOKS, inline_string_hooks_source(hooks))
    long_names, baked_tiles = long_names_source(Table(str(TABLE)), SMALL_FONT.read_bytes(), segments)
    write_if_changed(LONG_NAMES, long_names)
    write_if_changed(BAKED_TILES, baked_tiles)
    write_if_changed(NAMING_GRIDS, naming_grids_source(ROM.read_bytes(), Table(str(TABLE))))
    build_code("bl.s", variant)

    with variant.ips.open("wb") as f:
        writer = IPSWriter(f)
        writer.begin()
        f.write(ROOMS_PARTIAL.read_bytes())
        f.write(ips_records(variant.code_ips))
        f.write(text.getvalue())
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

    katsuji_build.build(katsuji_config.load(KATSUJI_CONFIG))

    # The dialogue font, the names and the layout code decide where dialog lines wrap (utils/dialog_layout.py)
    layout_sources = [KATSUJI_CONFIG, Path("fonts/fft.png"), Path("text/fr/names.xml"), *Path("utils").glob("*.py")]
    room_sources = [
        TABLE,
        *layout_sources,
        *Path("text/fr/dialog").glob("*.xml"),
        *Path("text/fr/battle").glob("*.xml"),
    ]
    if assets_need_refresh(room_sources, ROOMS_PARTIAL):
        build_rooms_partial(Table(str(TABLE)))

    build_ips(DEBUG if args.debug else RELEASE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
