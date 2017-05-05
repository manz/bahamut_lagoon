import struct
from utils.vm import NoMoreEventsForPlayer
from utils.vm.executor import walk_event_chain
from utils.vm.opcodes_map import opcode_table, opcode_names
from utils.vm.room import Room


def walk_events_for_player_event(room, player_event_id):
    room.pc = 0
    event_table_offset = room.get_word(6)
    room.program.put_reference(6, event_table_offset, comment='player events')

    room.pc = event_table_offset
    event_chain_addr = room.get_word(player_event_id * 2)

    if event_chain_addr != 0xFFFF:
        room.program.put_reference(event_table_offset + player_event_id * 2, event_chain_addr,
                                   comment=f'event chain for player {player_event_id}')
        room.pc = event_chain_addr
        walk_event_chain(room)
    else:
        room.program.put_reference(event_table_offset + player_event_id * 2, event_chain_addr,
                                   comment='End of players table')
        raise NoMoreEventsForPlayer()


def check_02(room):
    room.save_pc()
    room.pc = 0
    data_table_index = room.get_word(2)
    room.program.put_reference(2, data_table_index, comment='actors data')

    for k in range(0x17):
        room.pc = data_table_index
        try:
            d = room.get_word(k * 2)
        except struct.error:
            d = 0xFFFF
        room.program.put_reference(data_table_index + k * 2, d)
        if d == 0xFFFF:
            break
        room.pc = d
        data = room.get_data(0, 7)
        room.program.put_data(d, data)
        room.program.actors.add(k)
    room.restore_pc()


def check_0a(room):
    room.save_pc()
    room.pc = 0x0a

    index = room.get_word()
    if index != 0:
        room.pc = index
        while room.get_word() != 0xffff:
            room.save_pc()
            room.program.put_data(room.pc, room.get_data(size=7))
            room.pc = room.get_word(5)
            walk_event_chain(room)
            room.restore_pc()
            room.pc += 7
        room.program.put_data(room.pc, data=b'\xff\xff')
    room.restore_pc()


def check_04(room):
    room.save_pc()
    room.pc = 0x04
    room.pc = room.get_word()

    while room.get_word() != 0xffff:
        room.save_pc()
        room.program.put_data(room.pc, room.get_data(size=5))
        room.pc = room.get_word(3)
        walk_event_chain(room)
        room.restore_pc()
        room.pc += 5

    room.program.put_data(room.pc, data=b'\xff\xff')
    room.restore_pc()


def disassemble(room):
    header_length = room.get_word()
    if header_length > 2:
        room.program.put_reference(2, room.get_word(2), comment='room 2')
        check_02(room)
    if header_length > 6:
        room.program.put_reference(6, room.get_word(6), comment='room 6')
    if header_length > 8:
        room.program.put_reference(8, room.get_word(8), comment='room 8')

    room.pc = 0

    entry_point = room.get_word()
    room.program.put_reference(0, entry_point, comment='entry point')
    room.pc = entry_point
    walk_event_chain(room)

    if header_length > 4:
        room.pc = 0
        room.program.put_reference(4, room.get_word(4), comment='room 4')
        check_04(room)

    if header_length > 0xa:
        room.pc = 0
        room.program.put_reference(0xa, room.get_word(0xa), comment='room a')
        check_0a(room)

    if header_length > 8:
        room.pc = 0
        ptr = room.get_word(8)

        if ptr > 0:
            room.pc = ptr
            walk_event_chain(room)

    new_events = set(room.program.actors)
    if len(new_events) > 0:
        while True:
            try:
                for k in range(0, max(new_events) + 2):
                    walk_events_for_player_event(room, k)
                if not (new_events - room.program.actors):
                    break
            except NoMoreEventsForPlayer:
                break

    room.program.display_program()
    # room.program.compile('/tmp/out.bin')
    # with open('/tmp/{}.txt'.format(room.id), 'w', encoding='utf-8') as output:
    #     room.program.display_program(output)
    #     room.program.check_for_gaps()
    #     room.program.opcode_frequency()
    #     room.display_gathered_texts()


def live_disasm(room_id, data, suffix=''):
    room = Room(data, opcode_table, opcode_names, suffix)
    room.id = room_id
    disassemble(room)
    return room


def disasm_room(room_id, suffix=''):
    with open(f'../rooms{suffix}/{room_id:04d}.bin', 'rb') as un:
        room_data = un.read()
        if len(room_data) > 1:
            print('disasm', room_id)
            room = Room(room_data, opcode_table, opcode_names, suffix)
            room.id = room_id
            disassemble(room)


def disasm_rooms(suffix=''):
    # Nothing prevents uncompressed rooms to cross jump into another but the jump addresses cannot be the same across
    # rooms it might point to an error in disasm.
    forbidden_rooms = [
        79,
        81,  # actor table problem ?
        100,  # jump outside
        129,  # jump outside
        130,  # jump outside
        131,  # jump outside
        132,  # jump outside
        134,  # jump outside
        135,  # jump outside
        135,  # jump outside
        136,  # jump outside
        137,  # jump outside
        138,  # jump outside
        139,  # jump outside
        140,  # jump outside

    ]
    for room_id in range(0, 0xFE):
        if room_id not in forbidden_rooms:
            disasm_room(room_id, suffix=suffix)


if __name__ == '__main__':
    # disasm_rooms(suffix='_en')
    disasm_room(0, suffix='_fr')
