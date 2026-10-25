"""The battle banners (PLAYER PHASE, ENEMY PHASE, PLAYER WIN, GAME OVER): three compressed streams the E9FD60 commands
unpack when a banner shows.

- TILES (C6E000), the asset LZ (E9FB09): the banner's 4bpp tiles, to BG2's tiles at VRAM 0x3000.
- TILE_NUMBERS (C6EAB2), the interleaved LZ (E9FBA0): the asset LZ written to every other byte, so its back-references
  count in written bytes all the same; only 1B 00 01 ends it (a 1A word is always a back-reference). The low byte of
  each tilemap entry.
- FLIPS (C6ECF0), the asset LZ, then expanded by E9FC46: a byte, a u16 entry count / 4, then four 2-bit fields a byte,
  low bits first (1 flips horizontally, 2 vertically). Each field becomes an entry's high byte: field << 6 | the
  attribute (0x20, or 0x3C when $0538 is clear).

The tilemap is 32 entries wide, 128 rows, to BG2's map at VRAM 0x5000.
"""

from dataclasses import dataclass

from utils.cartridge import rom_offset
from utils.decompress_gfx import compress_asset

TILES = 0xC6E000
TILE_NUMBERS = 0xC6EAB2
FLIPS = 0xC6ECF0
ESCAPES = (0x1A, 0x1B)
END = 0x0100
FIELDS = 4  # flips a byte
FLIPS_HEADER = 3
# A stream's first byte: E9FD48 picks the decompressor from its low nibble.
ASSET_LZ = 0x00  # E9FB09
INTERLEAVED_LZ = 0x03  # E9FBA0
ATTRIBUTE = 0x20


def decompress(data: bytes, offset: int = 0, ends: tuple[int, ...] = ESCAPES) -> tuple[bytes, int]:
    """The asset LZ at `offset`, its first byte skipped, up to an `ends` byte with 00 01: the bytes it writes in
    order and the offset past it."""
    out = bytearray()
    x = offset + 1
    while True:
        control = data[x]
        if control not in ESCAPES:
            out.append(control)
            x += 1
            continue
        word = data[x + 1] | data[x + 2] << 8
        x += 3
        if word == 0:
            out.append(control)
        elif word == END and control in ends:
            return bytes(out), x
        else:
            _copy_back(out, control, data[x - 2], data[x - 1])


def _copy_back(out: bytearray, control: int, low: int, high: int) -> None:
    distance = (control & 1) << 10 | (low & 0xC0) << 2 | high
    for _ in range(low & 0x3F or 0x100):
        out.append(out[-distance])


def decompress_interleaved(data: bytes, offset: int = 0) -> tuple[bytes, int]:
    """The interleaved LZ (E9FBA0) at `offset`: the bytes it writes, every other byte in memory."""
    return decompress(data, offset, ends=(0x1B,))


def compress_interleaved(data: bytes) -> bytes:
    return compress_asset(data, end=0x1B)


def unpack_flips(packed: bytes) -> bytes:
    """An entry's flip field (0-3) for each entry of the FLIPS stream's bytes."""
    count = (packed[1] | packed[2] << 8) * FIELDS
    body = packed[FLIPS_HEADER:]
    return bytes(body[k // FIELDS] >> (2 * (k % FIELDS)) & 3 for k in range(count))


def pack_flips(flips: bytes, first: int = 0x04) -> bytes:
    """The FLIPS stream's bytes for `flips`, a multiple of 4 entries; `first` is the byte E9FC46 skips."""
    body = bytes(sum(flips[k + field] << (2 * field) for field in range(FIELDS)) for k in range(0, len(flips), FIELDS))
    return bytes([first]) + (len(body)).to_bytes(2, "little") + body


@dataclass(frozen=True)
class Banner:
    tiles: bytes  # 4bpp
    tile_numbers: bytes  # an entry's tile, its low byte
    flips: bytes  # an entry's flip field

    def tilemap(self, attribute: int = ATTRIBUTE) -> bytes:
        """The tilemap E9FD60 leaves for VRAM 0x5000."""
        return b"".join(bytes([n, f << 6 | attribute]) for n, f in zip(self.tile_numbers, self.flips, strict=True))

    def streams(self) -> tuple[bytes, bytes, bytes]:
        """TILES, TILE_NUMBERS and FLIPS compressed, each behind the format byte that picks its decompressor."""
        return (
            _with_format(ASSET_LZ, compress_asset(self.tiles)),
            _with_format(INTERLEAVED_LZ, compress_interleaved(self.tile_numbers)),
            _with_format(ASSET_LZ, compress_asset(pack_flips(self.flips))),
        )


def _with_format(format_byte: int, stream: bytes) -> bytes:
    """`stream` with its first byte, which the decompressors skip, set to `format_byte`."""
    return bytes([format_byte]) + stream[1:]


def read_banner(rom: bytes) -> Banner:
    tiles, _ = decompress(rom, rom_offset(TILES))
    tile_numbers, _ = decompress_interleaved(rom, rom_offset(TILE_NUMBERS))
    packed, _ = decompress(rom, rom_offset(FLIPS))
    return Banner(tiles, tile_numbers, unpack_flips(packed))
