"""
The battle script VM in game: scenario 00's battle, reached from the debug menu with its event skipped, opens with
the turn entries 0, 1, 2 of its script (Matelite's lines, the units moved around). Every instruction the VM fetches
(C0:6F33) sits where utils.vm.battle_script decodes one, with that opcode, and the turn (load_turn, $7E:3BD6) is 1.
"""

from tests.conftest import Console
from utils.battle_walk import room_script, walk

NEXT = 0xC06F33  # battle_opcode_runner's fetch
RUN_ENTRY = 0xC06ED8  # A = the header entry it runs
PC = 0x7E1A00
ROOM = 0x7FC080  # the unpacked room; its first word is the script's offset
TURN = 0x7E3BD6


def test_the_vm_runs_what_the_walk_decodes(console: Console) -> None:
    emu = console.emu
    console.load("debug-scenario-jump")
    console.press_until(console.button.DOWN, lambda: console.shows("JUMP TO SCENARIO  00"))
    console.press_until(console.button.A, lambda: console.shows("SKIP EVENT"))
    fetched: list[tuple[int, int]] = []
    entries: list[tuple[int, int]] = []

    def fetch(pc: int, value: int) -> None:
        address = emu.read16(PC)
        fetched.append((address - 0xC080 - emu.read16(ROOM), emu.read(0x7F0000 + address)))

    emu.add_exec_callback(NEXT, NEXT, fetch)
    emu.add_exec_callback(
        RUN_ENTRY, RUN_ENTRY, lambda pc, value: entries.append((emu.get_state().a & 0xFF, emu.read16(TURN)))
    )
    console.tap(console.button.B)  # skip the event, straight to the battle map
    for _ in range(40):  # A through the messages
        if len(entries) == 3 and fetched[-1][1] == 0xFF:
            break
        emu.run_frames(40)
        console.tap(console.button.A)

    code = walk(room_script(0)).code
    assert [(at, op) for at, op in fetched if at not in code or code[at].op != op] == []
    assert entries == [(0, 1), (1, 1), (2, 1)]
