import struct

from a816.cpu.cpu_65c816 import snes_to_rom, rom_to_snes, RomType
import xml.etree.ElementTree as ET

from a816.program import Program
from script import Table

from utils.vm.room import prettify

draw_inline_string_xrefs = [15626092, 15626155, 15626168, 15626212, 15626225, 15626272, 15626341, 15626406,
                            15626419, 15626531, 15626544, 15629211, 15629238, 15630172, 15630288, 15630773,
                            15630790, 15630809, 15630826, 15630847, 15630874, 15630907, 15630946, 15630983,
                            15631161, 15631180, 15631199, 15631225, 15631246, 15631263, 15631280, 15631317,
                            15633795, 15634295, 15634384, 15634425, 15635789, 15635918, 15636008, 15636049,
                            15636103, 15636176, 15636276, 15636322, 15636389, 15636447, 15636505, 15636563,
                            15636698, 15639826, 15640128, 15640154, 15640397, 15641666, 15642067, 15642122,
                            15642163, 15642230, 15642283, 15642338, 15642374, 15642424, 15642474, 15642524,
                            15642683, 15642700, 15644421, 15644520, 15644560, 15644621, 15644672, 15644723,
                            15644774, 15644878, 15644936, 15647141, 15649720, 15651484, 15651519, 15651554,
                            15651584, 15651599, 15651794, 15651819, 15651844, 15652215, 15652265, 15652309,
                            15653543, 15654266, 15654304, 15654319, 15654334, 15654351, 15655890, 15655948,
                            15656039, 15656227, 15656630, 15656651, 15656677, 15658920, 15658941, 15658967,
                            15659188, 15659203, 15659281, 15659298, 15659317, 15659336, 15659355, 15659372,
                            15659548, 15659578, 15659629, 15659646, 15659663, 15659680, 15659704, 15659717,
                            15659732, 15659751, 15659770, 15659804, 15659845, 15659866, 15661564]

feed_dragon_strings_xref = [12660474, 12678450, 12685102, 12685121, 12685140, 12685159, 12685178, 12685197, 12685216,
                            12685270, 12685289, 12685308, 12685327, 12685354, 12685563, 12688005, 12688048, 12688178,
                            12688197]


def read_word_backwards_from_xref(rom_file, xref, delta):
    rom_file.seek(xref - delta)
    return rom_file.read(1), rom_file.read(1)


def dragon_find_address(rom_file, xref):
    address_part = {}
    state = 'find_sta'
    current_byte_addr = None
    byte_addr = {}

    for delta in range(2, 80):
        data = read_word_backwards_from_xref(rom_file, snes_to_rom(xref), delta)
        # print(data)
        if state == 'find_sta':
            if data[0] == b'\x85':
                if data[1] in (b'\x60', b'\x5F', b'\x5E'):
                    state = 'find_lda'
                    current_byte_addr = ord(data[1])

        if state == 'find_lda':
            if data[0] == b'\xA9':
                address_part[current_byte_addr] = ord(data[1])
                byte_addr[current_byte_addr] = rom_file.tell() - 1
                if len(address_part.keys()) < 3:
                    state = 'find_sta'
                else:
                    break

    if {0x60, 0x5F, 0x5E} == set(address_part.keys()):
        return address_part[0x60] << 16 | address_part[0x5F] << 8 | address_part[0x5E], byte_addr
    else:
        raise RuntimeError('unable to find the required addresses part.')


def dump_char_names(rom_file):
    jp_fixed_table = Table('../text/table/dragon_feed_table.tbl')

    with open('../text/jp/names.xml', 'wt', encoding='utf-8') as char_names_jp:
        char_names = ET.Element('char_names')

        for k in range(40):
            rom_file.seek(snes_to_rom(0xEF0380) + k * 8)
            data_string = rom_file.read(8)
            string = ET.SubElement(char_names, 'string')
            data_string = data_string.rstrip(b'\xfe')
            string.text = jp_fixed_table.to_text(bytes(data_string))
        char_names_jp.write(prettify(char_names))


def insert_char_names(writer, address=None):
    jp_fixed_table = Table('./text/table/mz.tbl')
    address = address or snes_to_rom(0xEF0380)
    data = b''
    tree = ET.parse('./text/fr/names.xml')
    root = tree.getroot()

    for string in root:
        data += jp_fixed_table.to_bytes(string.text)[:8].ljust(8, b'\xfe')

    writer.write_block(data, address)


def dump_dragon_feed_inline_strings(rom_file):
    jp_fixed_table = Table('../text/table/dragon_feed_table.tbl')

    with open('../text/jp/dragon_feed.xml', 'wt', encoding='utf-8') as dragon_feed_jp:
        dragon_feed = ET.Element('dragon_feed')

        for xref in feed_dragon_strings_xref:
            addr, refs = dragon_find_address(rom_file, xref)
            # keep only addresses that look like rom
            # avoid ram
            if addr & 0x800000:
                print(f'ref {addr:#08x}')
                rom_file.seek(snes_to_rom(addr))

                read = b''
                data_string = b''

                while read != b'\xff':
                    read = rom_file.read(1)
                    data_string += read
                string = ET.SubElement(dragon_feed, 'string')
                string.set('ref_60', hex(refs[0x60]))
                string.set('ref_5f', hex(refs[0x5f]))
                string.set('ref_5e', hex(refs[0x5e]))
                string.set('xref', hex(xref))
                string.text = jp_fixed_table.to_text(bytes(data_string))
            else:
                print(f'ram ref {addr:#08x}')
        print(prettify(dragon_feed))
        dragon_feed_jp.write(prettify(dragon_feed))


def insert_dragon_feed_inline_strings(writer, address):
    jp_fixed_table = Table('./text/table/dragon_feed_table_mz.tbl')

    tree = ET.parse('./text/dragon_feed.xml')
    root = tree.getroot()

    text_data = b''

    for string in root:
        text_addr = rom_to_snes(len(text_data) + address, RomType.high_rom)
        text_data += jp_fixed_table.to_bytes(string.text)

        # patches LDAs for 24 bits address
        writer.write_block(bytes([(text_addr >> 16) & 0xFF]), int(string.get('ref_60'), 16))
        writer.write_block(bytes([(text_addr >> 8) & 0xFF]), int(string.get('ref_5f'), 16))
        writer.write_block(bytes([text_addr & 0xFF]), int(string.get('ref_5e'), 16))

    writer.write_block(text_data, address)


def dump_inline_string(rom_file, root, xref):
    rom_file.seek(snes_to_rom(xref) + 3)
    raw_string = b''
    while rom_file.peek(2)[:2] != b'\xff\xff':
        raw = rom_file.read(2)
        if raw != b'\x81\x40':
            raw_string += raw
        else:
            raw_string += b'\x20'

    jap_text = raw_string.decode('shift-jis')
    string = ET.SubElement(root, 'string')
    string.set('ref', hex(xref))
    string.set('jump_to', hex(rom_to_snes(rom_file.tell() + 2, RomType.high_rom)))
    string.text = jap_text


def dump_inline_strings(rom_file):
    with open('../text/jp/inline.xml', 'wt', encoding='utf-8') as inline_jp:
        inline = ET.Element('inline')

        for xref in draw_inline_string_xrefs:
            dump_inline_string(rom_file, inline, xref)

        inline_jp.write(prettify(inline))


def insert_inline_strings(writer, address, draw_inline_string_ref):
    jp_fixed_table = Table('./text/table/battle.tbl')
    tree = ET.parse('./text/inline.xml')
    root = tree.getroot()

    program_text_template = '''
*={draw_inline_string_xref:#02x}
{{
ret_addr = {return_address:#02x}
    jsr.w draw_inline_string_patched
    .dw {pointer:#02x}
    bra ret_addr
}}'''
    text_data = b''
    program_text = ''
    for string in root:
        program_text += program_text_template.format(
            draw_inline_string_xref=int(string.get('ref'), 16),
            pointer=rom_to_snes(address + len(text_data), RomType.high_rom) & 0xffff,
            return_address=int(string.get('jump_to'), 16)
        )
        text_data += jp_fixed_table.to_bytes(string.text) + b'\xff'

    program = Program()
    program.resolver.current_scope.add_symbol('draw_inline_string_patched', draw_inline_string_ref)
    program.assemble_string_with_emitter(program_text, 'generated_draw_inline.s', writer)

    writer.write_block(text_data, address)

    return rom_to_snes(address + len(text_data), RomType.high_rom)


def dump_message_strings(rom_file):
    with open('../text/en/messages.xml', 'wt', encoding='utf-8') as messages_jp:
        battle = ET.Element('messages')
        battle.set('pointers', hex(0xEE35F1))

        japanese_table = Table('../text/table/en.tbl')
        references = {}

        def put_reference(addr, index):
            if addr in references:
                references[addr].add(index)
            else:
                references[addr] = {index}

        strings = {}

        for pointer_id in range(630):
            rom_file.seek(snes_to_rom(0xEE35F1 + pointer_id * 2))

            ptr = struct.unpack('<H', rom_file.read(2))[0]
            put_reference(ptr, pointer_id)
            if ptr not in strings:
                rom_file.seek(snes_to_rom(0xED0000 + ptr))

                read = b''
                data_string = b''

                while read != b'\xff':
                    read = rom_file.read(1)
                    data_string += read
                strings[ptr] = data_string

        for addr in strings.keys():
            string = ET.SubElement(battle, 'string')
            refs = ET.SubElement(string, 'refs')
            for ref in references[addr]:
                ref_element = ET.SubElement(refs, 'ref')
                ref_element.text = hex(ref)
            data = ET.SubElement(string, 'data')
            data.text = japanese_table.to_text(strings[addr]).replace('\s', ' ')

        messages_jp.write(prettify(battle))


def insert_messages_strings(writer, address):
    mz_table = Table('./text/table/mz.tbl')
    tree = ET.parse('./text/messages.xml')
    root = tree.getroot()

    text_data = b''
    pointer_table = {}

    for string in root:
        refs = string.find('refs')
        data = string.find('data')

        text_addr = rom_to_snes(len(text_data) + address, RomType.high_rom)

        for ref in refs:
            pointer_id = int(ref.text, 16)
            pointer_table[pointer_id] = text_addr & 0xffff
        text_data += mz_table.to_bytes(data.text.replace(' ', '\s')) + b'\xff'

    pointer_table_bytes = b''
    for key in sorted(pointer_table):
        pointer = pointer_table[key]
        pointer_table_bytes += struct.pack('<H', pointer)

    # .EE:5404                 LDA     #$EE ; '¯'
    writer.write_block(bytes([rom_to_snes(address, RomType.high_rom) >> 16, 0]),
                       snes_to_rom(0xee5404 + 1))
    # .EE:553A                 LDA     #$EE ; '¯'
    writer.write_block(bytes([rom_to_snes(address, RomType.high_rom) >> 16, 0]),
                       snes_to_rom(0xee553A + 1))

    # battle magic description ?
    # .C0:D8AD                 LDA     word_EE0000, X
    writer.write_block(bytes([rom_to_snes(address, RomType.high_rom) >> 16]),
                       snes_to_rom(0xC0D8AD + 3))

    writer.write_block(pointer_table_bytes, snes_to_rom(int(root.get('pointers'), 16)))
    writer.write_block(text_data, address)

    return rom_to_snes(len(text_data) + address, RomType.high_rom)


def dump_battle_commands_strings(rom_file):
    jp_fixed_table = Table('../text/table/battle_jp.tbl')
    with open('../text/jp/battle.xml', 'wt', encoding='utf-8') as battle_jp:
        battle = ET.Element('battle')
        battle.set('pointers', hex(0xC0E121))
        battle.set('bank_addr', hex(0xC0E0FF))

        references = {}

        def put_reference(addr, index):
            if addr in references:
                references[addr].add(index)
            else:
                references[addr] = {index}

        strings = {}

        for k in range(24):
            rom_file.seek(snes_to_rom(0xC0E121 + k * 2))

            ptr = struct.unpack('<H', rom_file.read(2))[0]
            rom_file.seek(snes_to_rom(0xC00000 + ptr))
            put_reference(ptr, k)

            if ptr not in strings:

                data_string = b''
                byte = b''
                while byte not in (b'\xFF', b'\xFE'):
                    byte = rom_file.read(1)
                    data_string += byte
                strings[ptr] = data_string

        for addr in strings.keys():
            string = ET.SubElement(battle, 'string')
            refs = ET.SubElement(string, 'refs')
            for ref in references[addr]:
                ref_element = ET.SubElement(refs, 'ref')
                ref_element.text = hex(ref)
            data = ET.SubElement(string, 'data')
            data.text = jp_fixed_table.to_text(bytes(strings[addr]))

        battle_jp.write(prettify(battle))


def insert_battle_commands_strings(writer, address):
    jp_fixed_table = Table('./text/table/battle.tbl')
    tree = ET.parse('./text/battle.xml')
    root = tree.getroot()

    text_data = b''
    pointer_table = {}

    for string in root:
        refs = string.find('refs')
        data = string.find('data')

        text_addr = rom_to_snes(len(text_data) + address, RomType.high_rom)

        for ref in refs:
            pointer_id = int(ref.text, 16)
            pointer_table[pointer_id] = text_addr & 0xffff
        print(jp_fixed_table.to_bytes(data.text))
        text_data += jp_fixed_table.to_bytes(data.text)

    pointer_table_bytes = b''
    for key in sorted(pointer_table):
        pointer = pointer_table[key]
        pointer_table_bytes += struct.pack('<H', pointer)

    writer.write_block(bytes([rom_to_snes(address, RomType.high_rom) >> 16]),
                       snes_to_rom(int(root.get('bank_addr'), 16)))
    writer.write_block(pointer_table_bytes, snes_to_rom(int(root.get('pointers'), 16)))
    writer.write_block(text_data, address)

    return rom_to_snes(len(text_data) + address, RomType.high_rom)


def dump_fixed(rom_file, address, count, destination):
    pass


def dump_battle_fixed(rom_file):
    length = 8
    address = snes_to_rom(0xEF5920)

    jp_fixed_table = Table('../text/table/battle_jp.tbl')
    with open('../text/jp/battle-fixed.xml', 'wt', encoding='utf-8') as battle_fixed_jp:
        fixed = ET.Element('fixed')
        fixed.set('length', str(length))
        fixed.set('address', hex(address))

        for k in range(255):
            rom_file.seek(address + k * length)
            data = rom_file.read(length).split(b'\xff')[0]

            string = ET.SubElement(fixed, 'string')
            string.text = jp_fixed_table.to_text(data)
        battle_fixed_jp.write(prettify(fixed))


def insert_battle_fixed(writer, address=None):
    length = 8
    address = address or snes_to_rom(0xEF5920)
    jp_fixed_table = Table('./text/table/battle.tbl')
    tree = ET.parse('./text/battle-fixed.xml')
    root = tree.getroot()

    text_data = b''

    for string in root:
        data = jp_fixed_table.to_bytes(string.text)[:length]
        if len(data) < length:
            data += b'\xff'

        data = data.ljust(length, b'\xfe')
        text_data += data

    writer.write_block(text_data, address)


if __name__ == '__main__':
    with open('../bl.sfc', 'rb') as rom_file:
        dump_battle_fixed(rom_file)
        dump_dragon_feed_inline_strings(rom_file)
        dump_inline_strings(rom_file)
        dump_battle_commands_strings(rom_file)
        dump_char_names(rom_file)
        dump_message_strings(rom_file)

