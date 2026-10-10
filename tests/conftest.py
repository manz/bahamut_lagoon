"""
Shared kintsuki harness: one emulator per process, so every test drives the same one.

It runs the debug build (build/bl-debug.ips) and starts each test from a savestate in tests/savestates, as the
ff4 goldens do: a cold boot leaves WRAM to the emulator's RNG, and the game reads some of it uninitialised (the
title cursor, the debug scenario number). Some savestates come from older builds or other versions of the game: a
loaded one gets the French default names (party and saves, as utils/save_names.py gives a save) and a cleared
small_vwf, whose fields an older build laid out otherwise.
"""

import os
import re
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from script import Table

from utils.ips import apply_ips
from utils.name_tables import read_names
from utils.save_names import DEFAULT_NAMES, NAME_COUNT, TABLE, name_record, rename

REPO = Path(__file__).resolve().parents[1]
ROM = REPO / "build/bl.sfc"
DEBUG_IPS = REPO / "build/bl-debug.ips"
SYMBOLS = REPO / "build/bl-debug.sym"
SAVESTATES = Path(__file__).parent / "savestates"
GOLDENS = Path(__file__).parent / "goldens"
SYMBOL_LINE = re.compile(r"(?P<bank>[0-9a-f]{2}):\s*(?P<offset>[0-9a-f]+) (?P<label>\S+)$")
DEBUG_TABLE = REPO / "text/table/debug.tbl"

PARTY_NAMES = 0x7E2B00  # the names the player can change, 8 codes each
SAVES = 0x206000  # SRAM page 0: the save slots
SAVES_SIZE = 0x2000
SMALL_VWF_SOURCE = REPO / "src/small_vwf.s"
FIELD_SIZES = {"byte": 1, "word": 2, "long": 3}
FIELD = re.compile(r"^\s+(byte|word|long)(?:\[(.+)\])? (\w+)$")
CONSTANT = re.compile(r"^(\w+) = (\d+)", re.MULTILINE)
TILEMAP = 0x7EC000  # WRAM copy of the 32x32 BG tilemap the debug screens draw into
COLUMNS = 32


def symbol(name: str) -> int:
    """Bus address of a label in the debug build's symbol file."""
    for line in SYMBOLS.read_text().splitlines():
        match = SYMBOL_LINE.match(line)  # "ed:1101 battle_dma_transfer", offsets space-padded: "fe:   0 draw_string"
        if match and match["label"] == name:
            return int(match["bank"], 16) << 16 | int(match["offset"], 16)
    raise KeyError(name)


def small_vwf_fields() -> tuple[dict[str, int], int]:
    """SmallVwf's field offsets, read from its .struct, and its size."""
    source = SMALL_VWF_SOURCE.read_text()
    constants = {name: int(value) for name, value in CONSTANT.findall(source)}
    body = source.split(".struct SmallVwf {")[1].split("}")[0]
    offsets, offset = {}, 0
    for line in body.splitlines():
        match = FIELD.match(line)
        if match:
            offsets[match[3]] = offset
            count = eval(match[2], {}, constants) if match[2] else 1
            offset += FIELD_SIZES[match[1]] * count
    return offsets, offset


def _pixels(path: Path) -> bytes:
    from PIL import Image

    with Image.open(path) as image:
        return image.convert("RGB").tobytes()


class Console:
    """Drives the emulator and reads the debug screens back as text."""

    def __init__(self, emu, button) -> None:
        self.emu = emu
        self.button = button
        self.chars = {}
        for line in DEBUG_TABLE.read_text(encoding="utf-8").splitlines():
            code, _, char = line.partition("=")
            self.chars[int(code, 16)] = char

    def tap(self, button: int) -> None:
        self.emu.press(0, button)
        self.emu.run_frames(6)
        self.emu.release(0, button)
        self.emu.run_frames(20)

    def load(self, savestate: str) -> None:
        """Restore tests/savestates/<savestate>.kss, French names and a clear small_vwf in it, and let it settle a
        frame."""
        self.emu.load_state((SAVESTATES / f"{savestate}.kss").read_bytes())
        table = Table(str(TABLE))
        records = [name_record(table, name) for name in read_names(DEFAULT_NAMES)][:NAME_COUNT]
        self.emu.write_range(PARTY_NAMES, b"".join(records))
        self.emu.write_range(SAVES, rename(bytes(self.emu.read_range(SAVES, SAVES_SIZE)), records))
        self.emu.write_range(symbol("small_vwf"), bytes(small_vwf_fields()[1]))
        self.emu.run_frames(1)

    def press_until(self, button: int, done: Callable[[], bool], limit: int = 60) -> None:
        """Tap button until done(), checking before every tap so none carries past the target screen."""
        for _ in range(limit):
            if done():
                return
            self.tap(button)
            self.emu.run_frames(4)
        self.emu.screenshot(
            "/private/tmp/claude-501/-Users-manz-PyCharmProjects-bahamut-lagoon/d69b7309-07a4-48a8-8abc-9d7b5180c1fc/scratchpad/press-fail.png"
        )
        pytest.fail(f"{button} pressed {limit} times without reaching the screen:\n" + "\n".join(self.screen()))

    def screen(self) -> list[str]:
        tilemap = bytes(self.emu.read_range(TILEMAP, COLUMNS * COLUMNS * 2))
        return [
            "".join(self.chars.get(tilemap[(row * COLUMNS + col) * 2], "·") for col in range(COLUMNS)).rstrip("·")
            for row in range(COLUMNS)
        ]

    def shows(self, text: str) -> bool:
        return any(text in row for row in self.screen())

    def run_until(self, done: Callable[[], bool], limit: int = 900) -> None:
        for _ in range(0, limit, 5):
            if done():
                return
            self.emu.run_frames(5)
        pytest.fail(f"gave up after {limit} frames; screen:\n" + "\n".join(self.screen()))

    def matches_golden(self, name: str) -> bool:
        """Compare the screen with tests/goldens/<name>.png; UPDATE_GOLDENS=1 rewrites it, a mismatch leaves
        <name>.actual.png next to it."""
        golden = GOLDENS / f"{name}.png"
        actual = GOLDENS / f"{name}.actual.png"
        self.emu.screenshot(str(actual))
        if os.environ.get("UPDATE_GOLDENS") == "1" or not golden.exists():
            actual.replace(golden)
            return True
        same = _pixels(actual) == _pixels(golden)
        if same:
            actual.unlink()
        return same

    def count_calls(self, name: str) -> list[int]:
        """Record every execution of a label; returns the live list of frame numbers."""
        calls: list[int] = []
        address = symbol(name)
        self.emu.add_exec_callback(address, address, lambda pc, value: calls.append(self.emu.frame_count))
        return calls


@pytest.fixture(scope="session")
def console(tmp_path_factory) -> Iterator[Console]:
    kintsuki = pytest.importorskip("kintsuki")
    if not ROM.exists() or not DEBUG_IPS.exists():
        pytest.skip("needs build/bl.sfc and build/bl-debug.ips (./build.py --debug)")
    rom = tmp_path_factory.mktemp("rom") / "bl-debug.sfc"
    rom.write_bytes(apply_ips(ROM.read_bytes(), DEBUG_IPS.read_bytes()))
    emu = kintsuki.Emu(load_srm_sidecar=False)
    emu.load_rom(str(rom))
    yield Console(emu, kintsuki.Button)
