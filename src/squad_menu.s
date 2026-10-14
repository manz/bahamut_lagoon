"""
The battle squad menu (A on the map: Magies, Objets, Equiper, Infos), a bug of the original game: its task (block
0E80, a 0x40-byte stack at 14C0-14FF) calls an entry by hand, `phk / lda #$79CD / pha / jmp ($78E3,x)` (EE:79C2),
and Infos comes back to the loop top (EE:793E) through an rts that never pops that frame. Every visit to Infos
leaves 3 bytes; about twelve in one battle and the stack runs into task 0E00's, whose next resume returns into
00:0003 and the game hangs on a black screen. The unpatched game does it too.

The loop top now drops the dispatch frames left over it (EE:79CD, as pushed: CD 79 EE), then stops task 1100 as
the original did. A pass that came back through the dispatch's rtl has popped its frame: nothing to drop.
"""

.include "src/expansion.i"

_LEFT_FRAME = 0x79CD  ; the dispatch's return address minus one, its low word on the stack
_LEFT_BANK = 0xEE
_TASK_STOP = 0xEE44BD  ; jsl + the block's word inline

; EE:793E: jsl task_stop / .dw 0x1100, the loop top Infos and the dispatch's way back both reach.
.alloc at 0xEE793E {
    jsl.l squad_menu_loop_top
    nop
    nop
}

.alloc squad_menu in expansion {
squad_menu_loop_top:
"""Drop the dispatch frames left above the caller's own, then task_stop 1100. Leaves A 16-bit, as EE:793C does."""
    rep #0x20
_drop_frame:
    lda 0x04, s  ; under our return address: a left frame starts CD 79
    cmp.w #_LEFT_FRAME
    bne _no_frame
    lda 0x06, s
    and.w #0x00FF
    cmp.w #_LEFT_BANK
    bne _no_frame
    lda 0x01, s  ; our return address, 3 bytes up, over the left frame
    sta 0x04, s
    lda 0x02, s
    sta 0x05, s
    tsc
    clc
    adc.w #3
    tcs
    bra _drop_frame
_no_frame:
    jsl.l _TASK_STOP
    .dw 0x1100
    rtl
}
