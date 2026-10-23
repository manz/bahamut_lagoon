"""
The battle script VM in game.

Scenario 00's battle, reached from the debug menu with its event skipped, opens with the turn entries 0, 1, 2 of its
script (Matelite's lines, the units moved around). Every instruction the VM fetches (C0:6F33) sits where
utils.vm.battle_script decodes one, with that opcode, and the turn (load_turn, $7E:3BD6) is 1.

The other tests run scripts utils.vm.battle_asm assembles on scenario 00's battle map (tests/savestates/battle-map,
the player's turn): the phase routine's call to C0:9F3C is swapped for run_battle_entry once, on an entry pointed at
the script, and the test reads what it left in RAM. The VM's register lands in variables (store_var) to be read back.
"""

from collections.abc import Callable, Sequence

from tests.conftest import Console
from utils.battle_walk import room_script, walk
from utils.vm.battle_asm import Op, assemble, op

NEXT = 0xC06F33  # battle_opcode_runner's fetch
RUN_ENTRY = 0xC06ED8  # A = the header entry it runs
ENTRY_0C = 0xC06E70  # battle_entry_0c: sets the action arguments ($1A0C, $1A12) first
PHASE_CALL = 0xC09EE1  # the player phase routine's jsr C0:9F3C, once a frame
PC = 0x7E1A00
REG = 0x7E1A02
MODE = 0x7E1A05
ROOM = 0x7FC080  # the unpacked room; its first word is the script's offset
TURN = 0x7E3BD6
VARS = 0x7E3F90
DP = 0x7E0100  # the battle's direct page
CODE_AT = 0x24  # room 0's turn-start code, overwritten


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


class Script:
    """Runs assembled scripts on the battle map."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self.emu = console.emu
        console.load("battle-map")
        self.fetched: list[int] = []
        self.emu.add_exec_callback(NEXT, NEXT, lambda pc, value: self.fetched.append(self.emu.read16(PC)))

    def base(self) -> int:
        return 0x7F0000 + 0xC080 + self.emu.read16(ROOM)

    def run(
        self,
        items: Sequence[str | Op | bytes],
        entry: int = 0,
        via: int = RUN_ENTRY,
        prepare: Callable[[], None] | None = None,
        presses: Sequence[int | None] = (),
    ) -> None:
        """Run items (exit appended) as header entry `entry`, through `via` (run_battle_entry or an entry stub);
        `prepare` runs first, on the frame the script starts. Every 40 frames the next of `presses` (None: no tap),
        then A, is tapped to dismiss what waits."""
        emu = self.emu
        code, _ = assemble([*items, op("exit")], base=CODE_AT)
        emu.write_range(self.base() + CODE_AT, code)
        emu.write_range(self.base() + 2 * entry, CODE_AT.to_bytes(2, "little"))
        assert emu.run_until(PHASE_CALL, 600)
        if prepare:
            prepare()
        emu.push_word((PHASE_CALL + 2) & 0xFFFF)  # run as a jsr from the phase routine
        state = emu.get_state()
        state.pc = via
        state.a = state.a & 0xFF00 | entry
        emu.set_state(state)
        self.fetched.clear()
        buttons = iter(presses)
        for _ in range(60):
            emu.run_frames(10)
            if self.fetched and emu.read(0x7F0000 + self.fetched[-1]) == 0xFF:
                emu.run_frames(2)
                return
            if _ % 4 == 3 and (button := next(buttons, self.console.button.A)) is not None:
                self.console.tap(button)
        raise AssertionError("the script did not exit")

    def var(self, index: int, size: int = 1) -> int:
        return int.from_bytes(bytes(self.emu.read_range(VARS + index, size)), "little")

    def counting(self, address: int) -> Callable[[], int]:
        calls: list[int] = []
        self.emu.add_exec_callback(address, address, lambda pc, value: calls.append(pc))
        return lambda: len(calls)


def store(var: int) -> Op:
    return op("store_var", var)


def test_find_character_unit_finds_matelite_in_unit_1(console: Console) -> None:
    script = Script(console)
    script.run([op("find_character_unit", 0x03), store(0), op("find_character_unit", 0x7E), store(1)])
    assert (script.var(0), script.var(1)) == (0x01, 0xFF)


def test_unit_position_and_tile_occupant(console: Console) -> None:
    """Unit 0 (Byuu) stands at 0C, 09: the map byte there is 20 | unit, enemy units add 40."""
    script = Script(console)
    script.run(
        [
            op("load_unit_position", 0x00),
            store(0x80),  # a word: x, y
            op("load_tile_unit", 0x0C, 0x09),
            store(2),
            op("load_tile_unit", 0x09, 0x11),
            store(3),
            op("load_tile_unit", 0x0C, 0x05),
            store(4),
        ]
    )
    assert (script.var(0, 2), script.var(2), script.var(3), script.var(4)) == (0x090C, 0x20, 0x6C, 0x00)


def test_area_in_range_reads_the_range_layer(console: Console) -> None:
    """$7E:8001 marks the current range (here the move range around 0B-0D, 05-07): Z set when the rectangle has
    no marked tile."""
    script = Script(console)
    script.run(
        [
            op("load", 0),
            store(0),
            store(1),
            op("test_area_in_range", 0x0C, 0x05, 0x01, 0x01),
            op("jump_if_equal", "empty"),
            op("load", 1),
            store(0),
            "empty",
            op("test_area_in_range", 0x00, 0x00, 0x04, 0x04),
            op("jump_if_not_equal", "end"),
            op("load", 1),
            store(1),
            "end",
        ]
    )
    assert (script.var(0), script.var(1)) == (1, 1)


def test_hide_cursor_stops_the_map_cursor(console: Console) -> None:
    """C0:EB77 draws the map cursor; C0:EB65 skips it while mode bit 10 (or 20 / 40) is set. A script runs with bit
    80 alone, which leaves the cursor on, and exit clears them all."""
    script = Script(console)
    modes: list[int] = []
    console.emu.add_exec_callback(0xC0EB77, 0xC0EB77, lambda pc, value: modes.append(console.emu.read(MODE)))
    script.run([op("hide_cursor"), op("wait", 30), op("show_cursor"), op("wait", 30)])
    assert ({m for m in modes if m & 0x10}, modes.count(0x80) > 20) == (set(), True)


def test_spawn_unit_places_an_enemy_from_the_spawn_variables(console: Console) -> None:
    """Room 0's entry 0D spawn: type 17, vars 3A / 3B, flags E0 (set it up, at vars 3C / 3D, no fallback); then
    remove_unit takes it off the map again."""
    script = Script(console)
    enemy = 0x7E3750 + 0x20 * 0x10  # unit 10's record
    script.run(
        [
            *(op(name, value) for name, value in (("load", 0x17), ("store_var", 0x39), ("load", 0x02))),
            store(0x3A),
            op("load", 0x04),  # unit 0C + 4
            store(0x3B),
            op("load", 0x0C),
            store(0x3C),
            op("load", 0x05),
            store(0x3D),
            op("spawn_unit", 0xE0),
            store(0),
            op("spawn_unit", 0xE0),  # already on the map
            store(1),
            op("load_tile_unit", 0x0C, 0x05),
            store(2),
        ]
    )
    placed = (script.var(0), script.var(1), script.var(2), console.emu.read(enemy) & 0x80)
    script.run([op("select_unit", 0x10), op("remove_unit"), op("load_tile_unit", 0x0C, 0x05), store(3)])
    assert placed + (script.var(3), console.emu.read(enemy) & 0x80) == (0x10, 0xFF, 0x70, 0x00, 0x00, 0x80)


def test_give_item_adds_to_the_inventory(console: Console) -> None:
    script = Script(console)
    script.run([op("give_item", 0x04, 0x02), op("give_item", 0x04, 0x61)])
    assert bytes(console.emu.read_range(0x7E3AD0, 2)) == bytes([0x04, 0x63])  # capped at 99


def test_set_enemy_order_writes_enemy_records_only(console: Console) -> None:
    script = Script(console)
    script.run([op("set_enemy_order", 0x0D, 0x03), store(0), op("set_enemy_order", 0x01, 0x03), store(1)])
    order = console.emu.read(0x7E3750 + 0x20 * 0x0D + 0x10)
    assert (script.var(0), script.var(1), order) == (0x00, 0xFF, 0x03)


def test_map_event_applies_once_per_room_flag(console: Console) -> None:
    """Room 0's map event 3 ($7F:C282 + 3 * 4) uses room flag 4, still 00: F5 applies it without the redraw
    (C0:4047), flips the flag to FF and leaves $1A62 = FF. map_event redraws, but the flag no longer matches the
    event's bit 7 (0), so nothing happens until set_room_flag 84 clears it again."""
    script = Script(console)
    redraws = script.counting(0xC04047)
    flag = 0x7FC004
    script.run([op("map_event_f5", 0x03)])
    f5 = (redraws(), console.emu.read(flag), console.emu.read(0x7E1A62))
    script.run([op("map_event", 0x03)])
    again = (redraws() > 0, console.emu.read(flag))
    script.run([op("set_room_flag", 0x84)])
    cleared = console.emu.read(flag)
    script.run([op("map_event", 0x03)])
    assert (f5, again, cleared, console.emu.read(flag)) == ((0, 0xFF, 0xFF), (True, 0xFF), 0x00, 0xFF)


def test_action_arguments_reach_entry_0c(console: Console) -> None:
    """Entry 0C's stub copies the action ($3D) to $1A0C and its record's bytes +1, +2 (EF:4122) to $1A12: the
    element, then flags. Ice Breath Lv1 (8C), the scenario 00 dragon's, is ice (40), flags 40; Electron (8D) thunder
    (08), the element rooms 6, 13 and 20 test."""
    script = Script(console)
    console.emu.write(DP + 0x3D, 0x8C)
    script.run([op("load_action"), store(0), op("load_action_element"), store(0x81)], entry=0x0C, via=ENTRY_0C)
    ice = (script.var(0), script.var(1, 2))
    console.emu.write(DP + 0x3D, 0x8D)
    script.run([op("load_action_element"), store(0x81)], entry=0x0C, via=ENTRY_0C)
    assert ice + (script.var(1, 2),) == (0x8C, 0x4040, 0x4008)


def test_sound_and_shake_bytes(console: Console) -> None:
    script = Script(console)
    script.run(
        [
            op("sound_command", 0x00, 0x09, 0x80, 0x00),
            op("load_sound_byte", 0x01),
            store(0),
            op("shake_screen", 0x83),
            op("load_var", 0x00),  # keeps the shake on through a wait
            store(2),
        ]
    )
    shaking = console.emu.read(0x7E1A1E)
    script.run([op("stop_shake")])
    assert (script.var(0), shaking, console.emu.read(0x7E1A1E)) == (0x09, 0x83, 0x00)


def test_unit_sprite_is_saved_and_restored(console: Console) -> None:
    script = Script(console)
    record = 0x7E2B50  # unit 0
    sprite = console.emu.read(record + 0x08)
    script.run([op("set_unit_sprite", 0x00, 0x10)])
    changed = (console.emu.read(record + 0x08), console.emu.read(record + 0x1C))
    script.run([op("restore_unit_sprite", 0x00)])
    assert changed + (console.emu.read(record + 0x08),) == (0x10, sprite, sprite)


def test_load_terrain_reads_the_tile_tables(console: Console) -> None:
    """Scenario 00's river at 02, 0A: terrain 3 in both tables; x with bit 6 reads the tile under unit y."""
    script = Script(console)
    script.run(
        [
            op("load_terrain", 0x02, 0x0A),
            store(0x80),
            op("load_terrain", 0x40, 0x00),  # Byuu's tile
            store(0x82),
            op("load_terrain", 0x30, 0x00),  # off the map
            store(4),
            op("test_area_terrain", 0x00, 0x00, 0x08, 0x08),
            store(5),
            op("load_scenario"),
            store(6),
        ]
    )
    assert (script.var(0, 2), script.var(2, 2), script.var(4), script.var(5), script.var(6)) == (
        0x0303,
        0x0000,
        0xFF,
        0x00,
        0x00,
    )


def test_window_placement(console: Console) -> None:
    """$F7 places the message window: 01 at the top, A0 at the bottom (close_window puts A0 back). open_window picks
    the top one when $93 >= 0B (here 08: the bottom)."""
    script = Script(console)
    windows: list[int] = []
    console.emu.add_write_callback(0x0001F7, 0x0001F7, lambda address, value: windows.append(value))
    script.run([op("open_window_top"), op("close_window"), op("open_window_bottom"), op("close_window")])
    script.run([op("open_window"), op("close_window")])
    assert (windows, console.emu.read(DP + 0x93)) == ([0x01, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0], 0x08)


def test_unit_walk_off_removes_the_unit(console: Console) -> None:
    script = Script(console)
    script.run([op("select_unit", 0x0D), op("unit_walk_off", 0x04), op("load_tile_unit", 0x0D, 0x11), store(0)])
    assert (script.var(0), console.emu.read(0x7E3750 + 0x20 * 0x0D) & 0x80) == (0x00, 0x80)


def test_queue_scripted_action_fills_vars_28_to_2e(console: Console) -> None:
    script = Script(console)
    script.run([op("queue_scripted_action", 1, 2, 3, 4, 5, 6, 7)])
    assert bytes(console.emu.read_range(VARS + 0x28, 7)) == bytes(range(1, 8))


def test_victory_runs_entries_05_then_0d(console: Console) -> None:
    """The debug build's win (pad 2 B, C0:E617): entry 05 when the battle is won, the all-units experience window
    (C0:8849), then entry 0D once A closes it."""
    emu = console.emu
    console.load("battle-map")
    events: list[int | str] = []
    emu.add_exec_callback(RUN_ENTRY, RUN_ENTRY, lambda pc, value: events.append(emu.get_state().a & 0xFF))
    emu.add_exec_callback(0xC08849, 0xC08849, lambda pc, value: events.append("experience"))
    emu.press(1, console.button.B)
    emu.run_frames(10)
    emu.release(1, console.button.B)
    for _ in range(40):
        if 0x0D in events:
            break
        emu.run_frames(30)
        console.tap(console.button.A)
    assert events == [0x05, "experience", 0x0D]


def test_ice_freezes_the_river_and_fire_melts_it(console: Console) -> None:
    """An action's element (record +1) against the tile's terrain row (C0:44FF, $7E:6D10) flips the tile's state bit
    02: the dragon's Ice Breath (8C) freezes the river at 02, 0A, load_terrain then reads river 3 + 40, the ice
    bridge room 0 warns about; Hellfire (8B, fire) melts it again."""
    script = Script(console)
    area = [op("load", value) for value in (0x02, 0x0A, 0x01, 0x01)]  # vars 3C-3F: x, y, w, h
    river = [
        op("load_terrain", 0x02, 0x0A),
        store(0),
        op("test_area_terrain", 0x02, 0x0A, 0x01, 0x06),
        store(1),
        *(item for at, load in enumerate(area) for item in (load, store(0x3C + at))),
        op("test_area_terrain_vars"),
        store(2),
    ]
    script.run([op("select_unit", 0x06), op("use_action_at", 0x02, 0x0A, 0x8C), *river])
    frozen = (script.var(0), script.var(1), script.var(2))
    script.run([op("select_unit", 0x06), op("use_action_at", 0x02, 0x0A, 0x8B), *river])
    assert frozen + (script.var(0), script.var(1), script.var(2)) == (0x43, 0x01, 0x80, 0x03, 0x00, 0x00)


def test_unit_can_enter_reads_occupant_and_move_cost(console: Console) -> None:
    """test_unit_can_enter x, y, unit: 0 when the unit may stand there (or already does), 1 when an ally holds the
    tile, 80 for an enemy there or a tile its move type (map record +0x19) cannot cross (C0:4B05: cost 0), FF for
    an invalid unit."""
    script = Script(console)
    ally_x, ally_y = (console.emu.read(0x7E1400 + 0x20 + k) for k in (1, 2))  # unit 1's map record
    script.run(
        [
            op("test_unit_can_enter", 0x0C, 0x09, 0x00),  # Byuu's own tile
            store(0),
            op("test_unit_can_enter", ally_x, ally_y, 0x00),
            store(1),
            op("test_unit_can_enter", 0x09, 0x11, 0x00),  # enemy unit 0C
            store(2),
            op("test_unit_can_enter", 0x02, 0x0A, 0x00),  # the river
            store(3),
            op("test_unit_can_enter", 0x0C, 0x05, 0x00),
            store(4),
            op("test_unit_can_enter", 0x0C, 0x05, 0x1C),
            store(5),
            *(op(name, value) for name, value in (("load", 0x09), ("store_var", 0x3C), ("load", 0x11))),
            store(0x3D),
            op("load", 0x00),
            store(0x3A),
            op("test_unit_can_enter_vars"),  # x, y, unit from vars 3C, 3D, 3A
            store(6),
        ]
    )
    assert [script.var(k) for k in range(7)] == [0x00, 0x01, 0x80, 0x80, 0x00, 0xFF, 0x80]


def test_find_enemy_leader(console: Console) -> None:
    """Bit 2 of an enemy record marks the leader: find_enemy_leader returns it, and the battle is won once its
    characters are down (C0:E67C, the "defeat the leader" scenarios)."""
    script = Script(console)
    record = 0x7E3750 + 0x20 * 0x0D
    script.run([op("find_enemy_leader"), store(0)])
    script.run([op("find_enemy_leader"), store(1)], prepare=lambda: console.emu.write(record, 0x04))
    console.emu.write(record, 0x00)
    assert (script.var(0), script.var(1)) == (0xFF, 0x0D)


def test_ask_yes_no(console: Console) -> None:
    """ask_yes_no shows the prompt and a yes / no choice (C0:37F7, cursor `$B5` 3 / 4): Z set for yes, clear for
    no, N set when B cancels."""
    script = Script(console)
    button = console.button
    prompt: list[str | Op | bytes] = [
        op("ask_yes_no", "text"),
        op("jump_if_negative", "cancel"),
        op("jump_if_equal", "yes"),
        op("load", 0),
        op("jump", "end"),
        "yes",
        op("load", 1),
        op("jump", "end"),
        "cancel",
        op("load", 2),
        "end",
        store(0),
        op("exit"),
        "text",
        bytes([0xFF]) + bytes(0x1F),
    ]
    answers = []
    for presses in ((None, button.A), (None, button.DOWN, button.A), (None, button.B)):
        script.run(prompt, presses=presses)
        answers.append(script.var(0))
    assert answers == [1, 0, 2]


def test_set_unit_pose_holds_until_exit(console: Console) -> None:
    """set_unit_pose unit, kind plays animation `kind` (C6:B400) on the unit's map sprite in one of 8 slots
    ($1A68 = 80 | unit): kind 4 shows frame 4 and keeps it (map record +0x0C bit 0) until exit frees the slot."""
    script = Script(console)
    poses: list[int] = []
    console.emu.add_write_callback(0x00140C, 0x00140C, lambda address, value: poses.append(value))
    slots: list[tuple[int, int]] = []
    console.emu.add_write_callback(0x001A68, 0x001A6F, lambda address, value: slots.append((address, value)))
    script.run([op("set_unit_pose", 0x00, 0x04), op("wait", 10)])
    assert (poses, slots[-1]) == ([0x01, 0x00], (0x001A68, 0x80))


def test_sound_command_13_stops_the_music(console: Console) -> None:
    """Sound driver command 13 n (C3:0000, table C3:0883) fades the music out over n, at once with 0."""
    script = Script(console)
    playing = sum(voice.vol_l for voice in console.emu.dsp_voices())
    script.run([op("sound_command", 0x13, 0x00, 0x00, 0x00), op("wait", 30)])
    assert (playing > 0, sum(voice.vol_l for voice in console.emu.dsp_voices())) == (True, 0)


def test_a_defeated_unit_runs_entry_09(console: Console) -> None:
    """After an action, C0:D11B defeats every unit whose record +9 has bit 0 (its characters are down): record and
    map record bit 7, then entry 09 with $1A0E = the unit, here from inside the script's own use_action_at."""
    script = Script(console)
    emu = console.emu
    record = 0x7E3750 + 0x20 * 0x0D
    entries: list[tuple[int, int]] = []
    emu.add_exec_callback(
        RUN_ENTRY, RUN_ENTRY, lambda pc, value: entries.append((emu.get_state().a & 0xFF, emu.read(0x7E1A0E)))
    )
    script.run(
        [op("select_unit", 0x01), op("use_action_at", 0x0C, 0x0E, 0x35)],
        prepare=lambda: emu.write(record + 9, emu.read(record + 9) | 1),
    )
    assert (entries, emu.read(record) & 0x80) == ([(0x09, 0x0D)], 0x80)


def end_turn(console: Console) -> list[tuple[int, int | None]]:
    """End the player turn (START > end turn > yes), A through the dragons' and the enemies' phases until the next
    player phase (entry 02) waits for input: the entries run, with `$1A0E` for 07-0D (the unit; 00-05 leave it)."""
    emu = console.emu
    entries: list[tuple[int, int | None]] = []

    def entry(pc: int, value: int) -> None:
        index = emu.get_state().a & 0xFF
        entries.append((index, emu.read(0x7E1A0E) if index >= 0x07 else None))

    emu.add_exec_callback(RUN_ENTRY, RUN_ENTRY, entry)
    for button in (console.button.START, console.button.A, console.button.A):
        console.tap(button)
        emu.run_frames(30)
    for _ in range(200):
        emu.run_frames(30)
        if entries[-1:] == [(0x02, None)] and emu.read(0x7E0510) == 0:
            return entries
        console.tap(console.button.A)
    raise AssertionError(f"the turn did not end: {entries}")


def test_a_turn_runs_the_phase_entries(console: Console) -> None:
    """Turn 1 of scenario 00 ended: player_moved (07) for the units the dragon phase moves, the dragon that acts
    between before_action (0C) and player_acted (08), player_phase_end (03); each enemy runs enemy_moved (0A), the
    one in reach acts first (0C, enemy_acted 0B); turn_end (04), then turn 2 starts (00, 01, 02)."""
    console.load("battle-map")
    assert end_turn(console) == [
        *((0x07, unit) for unit in (0x00, 0x06, 0x02, 0x08)),
        (0x0C, 0x07),
        (0x08, 0x07),
        (0x07, 0x07),
        (0x03, None),
        (0x0A, 0x0C),
        (0x0A, 0x0D),
        (0x0C, 0x0E),
        (0x0B, 0x0E),
        (0x0A, 0x0E),
        (0x0A, 0x0F),
        (0x04, None),
        (0x00, None),
        (0x01, None),
        (0x02, None),
    ]


def test_enemy_order_4_holds_the_enemy(console: Console) -> None:
    """set_enemy_order writes the AI order (enemy record +0x10, C0:1B1E): 0 acts freely, 4 heads for the tile at
    record +0x0D / +0x0E and stays put when that is 0 (C0:1F5C). Unit 0E, ordered 4, neither attacks nor moves."""
    script = Script(console)
    emu = console.emu
    script.run([op("set_enemy_order", 0x0E, 0x04)])
    where = emu.read16(0x7E1400 + 0x20 * 0x0E + 1)
    entries = end_turn(console)
    assert ((0x0C, 0x0E) in entries, emu.read16(0x7E1400 + 0x20 * 0x0E + 1)) == (False, where)
