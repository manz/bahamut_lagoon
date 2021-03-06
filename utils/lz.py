import hashlib
import struct


def lz_decompress(data, decompressed=None):
    if decompressed is None:
        decompressed = bytearray()

    k = 0
    while k < len(data):
        control_byte = data[k]
        if control_byte == 0x00:
            raw_data = data[k + 1:k + 9]
            decompressed += raw_data
            k += 9
        else:
            k += 1
            for i in range(8):
                if k < len(data) - 1:
                    if (control_byte >> i) & 1:

                        back_pointer = (data[k] | (data[k + 1] << 8)) & 0x0FFF
                        length = ((data[k + 1] >> 4) & 0x0F) + 3

                        back_pointer = len(decompressed) - back_pointer

                        for l in range(length):
                            decompressed.append(decompressed[back_pointer + l])
                        k += 2
                    else:
                        decompressed.append(data[k])
                        k += 1

    return decompressed


def lz_decompress_battle(data, decompressed=None):
    if decompressed is None:
        decompressed = bytearray()

    k = 0
    while k < len(data):
        control_byte = data[k]
        if control_byte == 0x00:
            raw_data = data[k + 1:k + 9]
            decompressed += raw_data
            k += 9
        else:
            k += 1
            for i in range(8):
                if k < len(data):
                    if (control_byte >> i) & 1:

                        back_pointer = (data[k] | (data[k + 1] << 8)) & 0x0FFF
                        length = ((data[k + 1] >> 4) & 0x0F) + 3

                        back_pointer = len(decompressed) - back_pointer

                        for l in range(length):
                            decompressed.append(decompressed[back_pointer + l])
                        k += 2
                    else:
                        decompressed.append(data[k])
                        k += 1

    return decompressed


def find_pattern(buffer, temp_buffer):
    if len(buffer) > 0:
        for pattern_index in range(0, len(buffer)):
            pattern = buffer[pattern_index:]

            index = 0
            while index < len(temp_buffer):
                if pattern[index % len(pattern)] != temp_buffer[index]:
                    break
                index += 1

            if index > len(pattern):
                return len(pattern), index

    return None


def find_back_reference(data, position, search_patterns, buffer_size=4095, max_length=18, min_length=2):
    buffer = data[max(position - buffer_size, 0):position]
    retval = None

    temp_buffer = data[position:position + max_length]

    back_buffer = data[max(0, position - max_length): position]

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


def lz_compress(data, search_patterns=True):
    pos = 0
    compressed = bytearray()
    while pos < len(data):
        block = bytearray()
        block.append(0)
        k = 0
        while k < 8:
            back_reference = find_back_reference(data, pos, search_patterns=search_patterns)

            if back_reference and back_reference[1] > 2:
                block[0] |= 1 << k
                pointer = (back_reference[0]) + ((back_reference[1] - 3) << 12)
                block += struct.pack('<H', pointer)
                # if back_reference[0] < back_reference[1]:
                #     print(hex(pos), 'comp', back_reference[0], back_reference[1])
                pos += back_reference[1]
            else:
                try:
                    block.append(data[pos])
                except IndexError:
                    block.append(0xFF)
                pos += 1
            k += 1
        compressed += block

    return compressed


def get_sha(data):
    m = hashlib.sha1()
    m.update(data)
    return m.digest()
