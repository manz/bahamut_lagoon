"""The game's LZSS (rooms, battle rooms, graphics): katsuji's Lzss with a 12-bit window, 0 flag bits for literals
and the last flag group padded with FF. The room encoder also emits repeats of the bytes just before a position."""

from katsuji.codecs.lzss import Lzss

ROOMS = Lzss(window=0xFFF, literal=0, oldest=True, repeats=True, pad=0xFF)
GRAPHICS = Lzss(window=0xFFF, literal=0, oldest=True, repeats=False, pad=0xFF)


def lz_decompress(data: bytes | bytearray, decompressed: bytearray | None = None) -> bytearray:
    """Every item of the block `data`, appended to `decompressed`, which its references may reach into."""
    history = bytes(decompressed or b"")
    return bytearray(history + ROOMS.decompress(bytes(data), history=history)[0])


def find_pattern(buffer: bytes | bytearray, temp_buffer: bytes | bytearray) -> tuple[int, int] | None:
    if len(buffer) > 0:
        for pattern_index in range(len(buffer)):
            pattern = buffer[pattern_index:]

            index = 0
            while index < len(temp_buffer):
                if pattern[index % len(pattern)] != temp_buffer[index]:
                    break
                index += 1

            if index > len(pattern):
                return len(pattern), index

    return None


def find_back_reference(
    data: bytes | bytearray,
    position: int,
    search_patterns: bool,
    buffer_size: int = 4095,
    max_length: int = 18,
    min_length: int = 2,
) -> tuple[int, int] | None:
    buffer = data[max(position - buffer_size, 0) : position]
    retval: tuple[int, int] | None = None

    temp_buffer = data[position : position + max_length]

    back_buffer = data[max(0, position - max_length) : position]

    if search_patterns:
        repeating = find_pattern(back_buffer, temp_buffer)
    else:
        repeating = None

    for i in range(len(temp_buffer), min_length, -1):
        # find or rfind are usable here but rfind matches the dejap compressor
        # index = buffer.rfind(temp_buffer[:i])
        index = buffer.find(temp_buffer[:i])

        if index != -1:
            retval = len(buffer) - index, i
        if retval:
            if repeating and repeating[1] >= retval[1]:
                return repeating[0], repeating[1]
            else:
                return retval
        elif repeating and repeating[1] > min_length:
            return repeating[0], repeating[1]

    return None


def lz_compress(data: bytes | bytearray, search_patterns: bool = True) -> bytearray:
    return bytearray((ROOMS if search_patterns else GRAPHICS).compress(bytes(data)))
