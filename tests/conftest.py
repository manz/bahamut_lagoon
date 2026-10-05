"""
Shared kintsuki harness: one emulator per process, so every test drives the same one.

It runs the debug build (build/bl-debug.ips) and starts each test from a savestate in tests/savestates, as the
ff4 goldens do: a cold boot leaves WRAM to the emulator's RNG, and the game reads some of it uninitialised (the
title cursor, the debug scenario number).
"""

import os
import re
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from utils.ips import apply_ips

REPO = Path(__file__).resolve().parents[1]
ROM = REPO / "build/bl.sfc"
DEBUG_IPS = REPO / "build/bl-debug.ips"
SYMBOLS = REPO / "build/bl-debug.sym"
SAVESTATES = Path(__file__).parent / "savestates"
GOLDENS = Path(__file__).parent / "goldens"
SYMBOL_LINE = re.compile(r"(?P<bank>[0-9a-f]{2}):\s*(?P<offset>[0-9a-f]+) (?P<label>\S+)$")
DEBUG_TABLE = REPO / "text/table/debug.tbl"

TILEMAP = 0x7EC000  # WRAM copy of the 32x32 BG tilemap the debug screens draw into
COLUMNS = 32


def symbol(name: str) -> int:
    """Bus address of a label in the debug build's symbol file."""
    for line in SYMBOLS.read_text().splitlines():
        match = SYMBOL_LINE.match(line)  # "ed:1101 battle_dma_transfer", offsets space-padded: "fe:   0 draw_string"
        if match and match["label"] == name:
            return int(match["bank"], 16) << 16 | int(match["offset"], 16)
    raise KeyError(name)


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
        """Restore tests/savestates/<savestate>.kss and let it settle a frame."""
        self.emu.load_state((SAVESTATES / f"{savestate}.kss").read_bytes())
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
