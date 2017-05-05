from . import AlreadyVisitedError, DEBUG_OPCODES_TRACING


def walk_event_chain(room):
    while True:
        try:
            opcode = room.get_byte()

            opcode_name = room.opcode_names.get(opcode, 'opcode')

            if opcode == 0xFF:
                if DEBUG_OPCODES_TRACING:
                    print('[', hex(room.pc), ']', ':', opcode_name + '(', hex(opcode), ')')
                room.program.put_opcode(room.pc, 0xFF, [], size=1, comment='exit')
                break

            if DEBUG_OPCODES_TRACING:
                print('[', hex(room.pc), ']', ':', opcode_name + '(', hex(opcode), ')')
            delta = room.opcode_table[opcode].apply(room)
            room.pc += delta

        except AlreadyVisitedError:
            if DEBUG_OPCODES_TRACING:
                print('Jump to an already explored location backtracking !')
            break
    return room.pc
