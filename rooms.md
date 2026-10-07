# Bahamut Lagoon room scripts

Rooms are the field engine's scripts: events, dialogue, actor moves, scene changes. `room_opcodes.md` documents the
VM, the room header and every opcode, read from the handlers in bank DA.

## Storage

- `DA8000 + id×3`: 24-bit pointer to each room.
- `DA8300`: one bit per room, set when the room is LZ-compressed. The game decompresses it to 7F:A000
  (`prepare_room` DA1517), so a decompressed room must stay under 0x6000 bytes.
- The build stores a room uncompressed (and clears its bit) when the translated room outgrows that buffer.

## Tools

- `utils/dump_rooms.py` decompresses rooms and dumps their texts to `text/<lang>/dialog/<id>.xml`;
  `build_text_patch` writes the translated texts back.
- `utils/disasm.py` walks a room from every header slot (00-0C) and every jump target, as `utils/vm/opcodes_map.py`
  describes the opcodes. Texts are found only on reachable code.
- Translated texts replace the room from its lowest extracted text (the XML `base`) onward, and only the pointers
  listed in the XML are patched. A text the walker misses but that lies above the base is overwritten.
- `generate_macros.py` writes `src/room_macros.s`, one a816 macro per opcode; `src/test_room.s` and
  `src/test_actor_room.s` use them to write rooms by hand and check what an opcode does.
