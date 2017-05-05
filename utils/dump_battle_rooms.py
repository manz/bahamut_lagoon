import struct
from sys import stdout

from a816.cpu.cpu_65c816 import snes_to_rom

from utils.vm import AlreadyVisitedError
from utils.vm.executor import walk_event_chain
from utils.vm.opcodes_map import battle_opcode_table, battle_opcode_names
from utils.vm.room import Room


def lz_decompress(data, decompressed=None):
    if decompressed is None:
        decompressed = bytearray()

    k = 0
    while k < len(data):
        control_byte = data[k]
        if control_byte == 0x00:
            raw_data = data[k + 1:k + 9]
            decompressed += raw_data
            k += 9
        else:
            k += 1
            for i in range(8):
                if k < len(data):
                    if (control_byte >> i) & 1:

                        back_pointer = (data[k] | (data[k + 1] << 8)) & 0x0FFF
                        length = ((data[k + 1] >> 4) & 0x0F) + 3

                        back_pointer = len(decompressed) - back_pointer

                        for l in range(length):
                            decompressed.append(decompressed[back_pointer + l])

                        k += 2
                    else:
                        decompressed.append(data[k])
                        k += 1

    return decompressed


def decompress_block(rom):
    origin = rom.tell()

    size = rom.read(2)
    size = struct.unpack('<H', size)[0]
    print(hex(size))
    data = rom.read(size)
    decompressed = bytearray()
    decompressed = lz_decompress(data, decompressed)

    def get_size(count, control_byte):
        size = 0
        for i in range(count):
            if (control_byte >> i) & 1:
                size += 2
            else:
                size += 1
        return size + 1

    while True:
        control = rom.read(1)

        if control[0] != 0:
            next_end = rom.read(2)
            control_byte = rom.peek(1)

            next_size = get_size(control[0], control_byte[0])
            data = rom.read(next_size)

            decompressed = lz_decompress(data, decompressed)
        else:
            break
    return decompressed


def simulate_run(decompressed, run_opcode_addresses):
    opcodes = {}
    sorted_run_to_first_text = sorted(run_opcode_addresses)
    for k in range(len(sorted_run_to_first_text)):
        op_addr = sorted_run_to_first_text[k]

        opcode = decompressed[op_addr - 0x7FC080]
        try:
            # print(hex(op_addr - 0x7FC000))
            opcodes[opcode] = sorted_run_to_first_text[k + 1] - op_addr
            # print('{:#02x}: Opcode({}),'.format(opcode, sorted_run_to_first_text[k + 1] - op_addr))
        except IndexError:
            print(f'{opcode:#02x}')

    for key in sorted(opcodes.keys()):
        print(f'{opcode:#02x}: Opcode({opcodes[key]}),')


def walk_battle_room(room_id, decompressed):
    addr = struct.unpack('<H', decompressed[:2])[0]

    decompressed_program = decompressed[addr:]
    room = Room(decompressed_program, battle_opcode_table, battle_opcode_names, suffix=SUFFIX)
    room.id = room_id
    ptr_table = []
    for k in range(0, 0x0c + 2):
        room.pc = 0
        try:
            addr = room.get_word(k * 2)
            room.program.put_reference(k * 2, addr, f"entry {k:#02x}")

            room.jump_to(addr)
            # print('PC {:04x} {}'.format(addr, k))

            walk_event_chain(room)
        except AlreadyVisitedError:
            pass

    return room

    # program.display_program_part(stdout, text_program)
    # with open('/tmp/b{}.txt'.format(room.id), 'w', encoding='utf-8') as output:
    #     room.program.display_program(output)


def dump_battle_room(rom, room_id=0):
    table_entry = snes_to_rom(0xc7140f)
    rom.seek(table_entry + (room_id * 3))
    ptr = rom.read(3)
    address = snes_to_rom(ptr[0] + (ptr[1] << 8) + (ptr[2] << 16))
    print(hex(address))

    rom.seek(address)
    try:
        decompressed = decompress_block(rom)
    except IndexError as e:
        print(f'Unable to decompress: {e}')
    # simulate_run(decompressed)
    else:
        try:
            room = walk_battle_room(room_id, decompressed)
            program = room.program

            if True or SUFFIX == '_fr':
                text_program = room.program.filter(lambda _, e: e[0][0] == 'text')
                first_text_address = sorted(text_program.keys())[0]
                program.display_program_part(stdout, text_program)

                text_block = room.room[first_text_address:]
                print(room.table.to_text(bytes(text_block)).replace('\\s', ' '))
            else:
                texts = room.dump_text()
                if texts:
                    with open('../rooms{}/b{:04d}.xml'.format(SUFFIX, room_id), 'wt', encoding='utf-8') as output:
                        output.write(texts)
        except AlreadyVisitedError:
            pass

        with open('/tmp/battle.bin', 'wb') as out:
            out.write(decompressed)


if __name__ == '__main__':
    SUFFIX = '_en'
    # with open('../bahamut_tt.smc', 'rb') as rom_file:
    # seems like there is only 35 battle rooms.
    with open('../ble_snes.sfc', 'rb') as rom_file:
        for k in range(0, 32):
            print(f'{k} ' + '-' * 80)
            try:
                dump_battle_room(rom_file, room_id=k)
            except IndexError as e:
                print(e)
                print('far jump ?')
