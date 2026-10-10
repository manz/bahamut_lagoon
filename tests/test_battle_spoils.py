"""
Scenario 00's first combat, from the dragons' turn before it: the spoils window after the fight (C17514) labels the
gold "GP", two characters, which the C1 engine draws itself. c1_vwf's hook used to sit on that drawing loop's first
instruction, so the fallback jumped into the hook's own operand and the copy ran on through memory: the battle never
came back to the map.
"""

AI_TURN = 0x7E0510  # 1 while the dragons and the enemies act, 0 on the player's turn
DRAW_STRING = 0xC12DDA  # C1 engine: draw [$5E]
SPOILS_BANK = 0xFC  # the relocated dragon feed strings, "GP" among them (build.py)


def test_combat_spoils_return_to_the_map(console):
    console.load("battle-exp")
    spoils: list[int] = []
    emu = console.emu
    emu.add_exec_callback(
        DRAW_STRING,
        DRAW_STRING,
        lambda pc, value: spoils.append(emu.frame_count) if emu.read(0x60) == SPOILS_BANK else None,
    )
    golden = False
    for _ in range(60):  # a minute: the fight, its spoils, the rest of the enemies' turn
        if emu.read(AI_TURN) == 0:
            break
        console.tap(console.button.A)
        console.emu.run_frames(28)
        if spoils and not golden:
            golden = console.matches_golden("battle-spoils")
    assert spoils
    assert golden
    assert emu.read(AI_TURN) == 0
