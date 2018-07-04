; patch sprite params
{
*=0xD5F595
    .dw new_game_sprite_struct & 0xffff
    .dw load_game_sprite_struct & 0xffff
    .dw temporally_play_sprite_struct & 0xffff

*=0xD5F5CD
    .dw ex_play_sprite_struct & 0xffff
*=0xD5F6FF
temporally_play_sprite_struct:
    .db 5

    .db 0xF8
    .db 0xE0
    .db 0x3e ; sprite id

    .db 0xF8
    .db 0xF0
    .db 0x3f ; sprite id

    .db 0xF8
    .db 0xf8
    .db 0x3a

    .db 0xF8
    .db 0x8
    .db 0x3b

    .db 0xF8
    .db 0x18
    .db 0x3c

ex_play_sprite_struct: ; 3
    .db 3
    .db 0xf8
    .db 0xe0
    .db 0x3d

    .db 0xf8
    .db 0xf0
    .db 0x3e

    .db 0xf8
    .db 0
    .db 0x3f
another_end:

*=0xD5FFDE
new_game_sprite_struct:
    .db 0x4 ; array length

    .db 0xF8
    .db 0xE0
    .db 0x36 ; sprite id

    .db 0xF8
    .db 0xF0
    .db 0x37 ; sprite id

    .db 0xF8
    .db 0x0
    .db 0x3e ; sprite id

    .db 0xF8
    .db 0x10
    .db 0x3f ; sprite id

load_game_sprite_struct:
    .db 0x4 ; array length

    .db 0xF8
    .db 0xE0
    .db 0x38 ; sprite id

    .db 0xF8
    .db 0xF0
    .db 0x39 ; sprite id

    .db 0xF8
    .db 0xff
    .db 0x3e ; sprite id

    .db 0xF8
    .db 0x0f
    .db 0x3f ; sprite id

}
;.D5:F6FF                 .BYTE   2
;.D5:F700                 .BYTE $F8
;.D5:F701                 .BYTE $E0 ; Ó
;.D5:F702                 .BYTE $36 ; 6           ; and 0xC0 -> 0xf
;.D5:F702                                         ; and 0x3f -> A
;.D5:F703                 .BYTE $F8 ; °
;.D5:F704                 .BYTE $F0 ; ­
;.D5:F705                 .BYTE $37 ; 7


