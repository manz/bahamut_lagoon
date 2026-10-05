"""
Debug mode menus in English.

The debug screens (scenario jump, start/end event, event/unit numbers, battle/event test) draw 8x8 text from bank
C0, so the English strings go in the bank C0 padding below the cartridge header. Only reachable with DEBUG set,
but built either way so flipping the flag never shows Japanese.
"""


.pool c0_padding {
    range 0xC0FD80 0xC0FF9F
    strategy order
}

.table "text/table/debug.tbl"

NEWLINE = 0xFE  ; next tilemap row
END_OF_TEXT = 0xFF

.alloc debug_menu_text in c0_padding {
jump_to_scenario:
    .text "JUMP TO SCENARIO"
jump_to_scenario_end:

test_menu:
    .text "BATTLE TEST     A"
    .db NEWLINE, NEWLINE
    .text "EVENT TEST      X"
    .db NEWLINE, NEWLINE
    .text "BACK TO FIELD   B"
    .db END_OF_TEXT

event_numbers:
    .text "EVENT NO"
    .db NEWLINE, NEWLINE
    .text "UNIT NO"
    .db END_OF_TEXT

start_event:
    .text "START EVENT"
    .db NEWLINE, NEWLINE
    .text "WATCH EVENT  A"
    .db NEWLINE, NEWLINE
    .text "SKIP EVENT   B"
    .db NEWLINE, NEWLINE
    .text "MAP ONLY     Y"
    .db END_OF_TEXT

end_event:
    .text "END EVENT"
    .db NEWLINE, NEWLINE
    .text "WATCH EVENT  A"
    .db NEWLINE, NEWLINE
    .text "SKIP EVENT   B"
    .db END_OF_TEXT
}

; Scenario jump: a fixed-length copy loop, 12 chars from column 10 in Japanese. The English label starts at
; column 6 so it still ends before the scenario number at column 24.
.alloc at 0xC0AF88 {
    ldy.w #0xC40C
    ldx.w #jump_to_scenario & 0xFFFF
}
.alloc at 0xC0AFA3 {
    cpx.w #jump_to_scenario_end & 0xFFFF
}

; Event / unit numbers.
.alloc at 0xC0CF4B {
    ldx.w #event_numbers & 0xFFFF
}

; Start / end event.
.alloc at 0xC0CF6D {
    ldx.w #start_event & 0xFFFF
}
.alloc at 0xC0CF74 {
    ldx.w #end_event & 0xFFFF
}

; Start / end event number: column 19 -> 22, past the longer English header.
.alloc at 0xC0CF34 {
    sta.l 0x7EC42C
}
.alloc at 0xC0CF40 {
    sta.l 0x7EC42E
}

; Battle / event test.
.alloc at 0xC0CF96 {
    ldx.w #test_menu & 0xFFFF
}

; Position errors, overwritten in place: the code fills the digits at fixed offsets.
.alloc at 0xC0EDC7 {
    .text "ERR1"
}
.alloc at 0xC0EDE0 {
    .text "ERR2"
}
