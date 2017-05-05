#!/usr/bin/env python3
import struct
from a816.cpu.cpu_65c816 import RomType
from a816.program import Program
from a816.writers import SFCWriter, IPSWriter
from io import BytesIO

from utils.dump_rooms import build_text_patch
from utils.lz import lz_compress, lz_decompress

predefined_symbols = {
    'DEBUG': 0,
    'DATA': 0
}


def build_assembly(input, output, writer):
    asm = Program()
    asm.resolver.rom_type = RomType.high_rom
    asm.assemble_with_emitter(input, writer)


# def build_room(input, output):
#     asm = Program()
#     asm.resolver.rom_type = RomType.high_rom
#     buffer = BytesIO()
#     sfc_emiter = SFCWriter(buffer)
#     asm.assemble_with_emitter(input, sfc_emiter)
#
#     buffer.seek(0)
#     uncompressed_data = buffer.read()
#
#     with open('/tmp/uncompressed.bin', 'wb') as uncompressed:
#         uncompressed.write(uncompressed_data)
#
#     with open(output, 'wb') as fd:
#         compressed = lz_compress(uncompressed_data) + b'\x00'
#         compressed = struct.pack('<H', len(compressed) - 1) + compressed
#         # fd.write()
#         # fd.write(compressed)
#         fd.write(compressed)

if __name__ == '__main__':
    with open('bl.ips', 'wb') as f:
        writer = IPSWriter(f)
        writer.begin()

        with open('bl.sfc', 'rb') as rom:
            build_text_patch(rom, writer, '_mz')
        build_assembly('bl.s', 'bl.ips', writer)

        writer.end()
