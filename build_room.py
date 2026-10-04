#!/usr/bin/env python3
"""
Build room assembly files with a816 and patch into ROM
"""

import os
import subprocess
import struct
import a816
from a816.program import Program


def build_room(asm_file, output_bin):
    """Assemble room file with a816"""

    program = Program()

    exit_code = program.assemble(asm_file, output_bin)

    return exit_code == 0


def patch_room_into_rom(room_bin, rom_file, room_offset):
    """Patch assembled room into ROM at specified offset"""
    if not os.path.exists(room_bin):
        print(f"Error: Room binary {room_bin} not found")
        return False

    if not os.path.exists(rom_file):
        print(f"Error: ROM file {rom_file} not found")
        return False

    # Read room data
    with open(room_bin, "rb") as f:
        room_data = f.read()

    # Read ROM
    with open(rom_file, "r+b") as f:
        f.seek(room_offset)
        f.write(room_data)

    print(f"Patched {len(room_data)} bytes at offset {room_offset:#x}")
    return True


def main():
    """Build and optionally patch test room"""
    import sys

    # Allow specifying which room to build
    if len(sys.argv) > 1:
        room_name = sys.argv[1]
        asm_file = f"src/{room_name}.s"
        bin_file = f"build/{room_name}.bin"
    else:
        asm_file = "src/test_room.s"
        bin_file = "build/test_room.bin"

    # Create build directory
    os.makedirs("build", exist_ok=True)

    # Build room
    if build_room(asm_file, bin_file):
        print(f"Room built successfully: {bin_file}")

        # Show hex dump of result
        if os.path.exists(bin_file):
            with open(bin_file, "rb") as f:
                data = f.read()

            print("\nHex dump of compiled room:")
            for i in range(0, len(data), 16):
                chunk = data[i : i + 16]
                hex_str = " ".join(f"{b:02X}" for b in chunk)
                print(f"{i:04X}: {hex_str}")

        # TODO: Add ROM patching when ROM file is available
        # patch_room_into_rom(bin_file, "bl.sfc", 0x100000)


if __name__ == "__main__":
    main()
