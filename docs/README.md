# Bahamut Lagoon

## Assets
Main Font `0xED0005`

## Dialog Rooms
The rooms might be compressed


## Room compression
```ca65
lda [0x76], x
```

At this time the long address behind `0x76` is `0x7FAXYY` look in the memory editor and look around. `0x7FA000` seems to do the trick
Or look in IDA.

Search where the data come from, put a write breakpoint on `0x7FA000`.

The routine looks like it's an _LZSS_ decompressor.

After a little digging the first two bytes are the decompressed length.


```python
def lz_decompress(data, decompressed=None):
    if decompressed is None:
        decompressed = bytearray()

    k = 0
    while k < len(data):
        control_byte = data[k]
        if control_byte == 0x00:
            k += 9
        else:
            k += 1
            raw_data = data[k + 1:k + 9]
            decompressed += raw_data
            for i in range(8):
                if k < len(data)-1:
                    if (control_byte >> i) & 1:
                        back_pointer = (data[k] + (data[k + 1] << 8)) & 0x0FFF
                        length = ((data[k + 1] >> 4) & 0x0F) + 3

                        back_pointer = len(decompressed) - back_pointer
                        pointed_data = decompressed[back_pointer:back_pointer + length]

                        decompressed += pointed_data
                        k += 2
                    else:
                        decompressed.append(data[k])
                        k += 1

    return decompressed
```

## Room Structure

More half of the room is not textual data, in fact it's code but not native to the cpu these are game specific opcodes.
This is the equivalent of an engine scripting interface.

An init routine, and a "main".

the "main" part is what would seem "automatic" for example at the beginning of the first room (Downfall of Kahna Castle).

Everything that shows on screen is driven by this script. (if it's script we can write some)

### The "Events":
- Events based on the position on the main character
- Events triggered by the player (Talk to someone)

### Header
- 0x0000 main entry point (0x08 or 0x0c)
- 0x0002 actors table
- 0x0004 
- 0x0006 player events ?
- 0x0008 
- 0x000a
- 0x000c


### Opcodes



## Strange Calling Convention

Heavily used in script interpreter .

The principle is to abuse the RTS  instruction, and thus the stack. It's quite simple, push on the stack addresses and use RTS to change the program counter.

The main advantage of this method is that it hinders the disassembly, by loosing JSR we loose the indication of the call. And the code is much harder to follow.

```ca65
sick_caller:
    php
    phx
    phy
    lda #ret
    dec
    pha
    
    lda #another_func # this can be in the work ram (or virtually every where)
    dec
    pha
    
    rts
ret:
    plx
    ply
    plp
    rts
```
