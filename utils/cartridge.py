"""ROM addressing through the cartridge bus declared in a816.toml."""

from functools import cache
from pathlib import Path

from a816.config import discover_a816_config
from a816.cpu.mapping import Bus
from a816.mappers import map_on_bus

# The game and the patch address the ROM through its FastROM banks C0-FF.
ROM_BANKS = 0xC00000


@cache
def cartridge_bus() -> Bus:
    """The bus a816 assembles against, built from the project's a816.toml."""
    config = discover_a816_config(Path(__file__).parent)
    if config is None or not config.bus_map:
        raise RuntimeError("a816.toml with a board is required to address the ROM")
    bus = Bus("cartridge")
    for mapping in config.bus_map:
        map_on_bus(bus, mapping)
    return bus


def rom_offset(address: int) -> int:
    """File offset of a bus address that reads the ROM."""
    physical = cartridge_bus().get_address(address).physical
    if physical is None:
        raise ValueError(f"{address:#08x} does not address the ROM")
    return physical


def rom_address(offset: int) -> int:
    """Bus address of a file offset, in the ROM banks C0-FF."""
    region = cartridge_bus().get_address(ROM_BANKS).mapping
    return region.logical_address(offset, near=ROM_BANKS)
