from a816.cpu.cpu_65c816 import rom_to_snes, RomType

if __name__ == "__main__":
    print(hex(rom_to_snes(0x974E5, RomType.low_rom)))
