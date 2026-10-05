"""
Title screen: sprite lists for the translated menu entries.

Each list is a count, then that many MenuSprite: y and x are signed offsets from the menu entry (y 0xF8 is 8px
up), tile the sprite tile.
"""


.struct MenuSprite {
    byte y
    byte x
    byte tile
}

; patch sprite params
{
    .alloc at 0xD5F595 {
    .dw new_game_sprite_struct & 0xffff
    .dw load_game_sprite_struct & 0xffff
    .dw temporally_play_sprite_struct & 0xffff
    }
    .alloc at 0xD5F5CD {
    .dw ex_play_sprite_struct & 0xffff
    }
    .alloc at 0xD5F6FF {
temporally_play_sprite_struct:
    .db 5
    .istruct MenuSprite {
        y = 0xF8
        x = 0xE0
        tile = 0x3E
    }
    .istruct MenuSprite {
        y = 0xF8
        x = 0xF0
        tile = 0x3F
    }
    .istruct MenuSprite {
        y = 0xF8
        x = 0xF8
        tile = 0x3A
    }
    .istruct MenuSprite {
        y = 0xF8
        x = 0x08
        tile = 0x3B
    }
    .istruct MenuSprite {
        y = 0xF8
        x = 0x18
        tile = 0x3C
    }
ex_play_sprite_struct:
    .db 3
    .istruct MenuSprite {
        y = 0xF8
        x = 0xE0
        tile = 0x3D
    }
    .istruct MenuSprite {
        y = 0xF8
        x = 0xF0
        tile = 0x3E
    }
    .istruct MenuSprite {
        y = 0xF8
        x = 0x00
        tile = 0x3F
    }
    }
    .alloc at 0xD5FFDE {
new_game_sprite_struct:
    .db 4
    .istruct MenuSprite {
        y = 0xF8
        x = 0xE0
        tile = 0x36
    }
    .istruct MenuSprite {
        y = 0xF8
        x = 0xF0
        tile = 0x37
    }
    .istruct MenuSprite {
        y = 0xF8
        x = 0x00
        tile = 0x3E
    }
    .istruct MenuSprite {
        y = 0xF8
        x = 0x10
        tile = 0x3F
    }
load_game_sprite_struct:
    .db 4
    .istruct MenuSprite {
        y = 0xF8
        x = 0xE0
        tile = 0x38
    }
    .istruct MenuSprite {
        y = 0xF8
        x = 0xF0
        tile = 0x39
    }
    .istruct MenuSprite {
        y = 0xF8
        x = 0xFF
        tile = 0x3E
    }
    .istruct MenuSprite {
        y = 0xF8
        x = 0x0F
        tile = 0x3F
    }
    }
}

;.D5:F6FF                 .BYTE   2
;.D5:F700                 .BYTE $F8
;.D5:F701                 .BYTE $E0 ; Ó
;.D5:F702                 .BYTE $36 ; 6           ; and 0xC0 -> 0xf
;.D5:F702                                         ; and 0x3f -> A
;.D5:F703                 .BYTE $F8 ; °
;.D5:F704                 .BYTE $F0 ; ­
;.D5:F705                 .BYTE $37 ; 7
