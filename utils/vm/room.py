import os
import struct

from script import Table

from utils.vm import AlreadyVisitedError
from .program import Program

import xml.etree.ElementTree as ET
from xml.dom import minidom

text_path = os.path.join(os.path.dirname(__file__), '../../text')

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")


class Room(object):
    def __init__(self, room, opcode_table, opcode_names, suffix):

        self.table = Table(os.path.join(text_path, f'table{suffix}.tbl'))
        self.room = room #+ b'\xff' * 255
        self.suffix = suffix
        self.pc = 0
        self.texts = {}
        self.references = {}
        self.stack = []
        self.code = {}
        self.jump_addresses = []
        self.program = Program(self, opcode_names)
        self._pc = []
        self.opcode_table = opcode_table
        self.opcode_names = opcode_names
        self.id = 0

    def save_pc(self):
        self._pc.append(self.pc)

    def restore_pc(self):
        self.pc = self._pc.pop()

    def push_addr(self, address):
        self.stack.append(address)

    def pop_addr(self):
        return self.stack.pop()

    def jump_to(self, address):
        if address in self.jump_addresses:
            raise AlreadyVisitedError()
        self.pc = address
        self.jump_addresses.append(address)
        self.program.put_label(address)

    def put_text_reference(self, code_position, pointer, text):
        if pointer in self.references:
            self.references[pointer] = set(list(self.references[pointer]) + [code_position])
        else:
            self.references[pointer] = {code_position}

        self.texts[pointer] = text

        self.program.put_text_pointer(pointer, code_position)

    def get_byte(self, delta=0):
        hack = False

        if hack:
            try:
                data = self.room[self.pc + delta]
            except IndexError:
                return 0xff

        data = self.room[self.pc + delta]

        return data

    def get_word(self, delta=0):
        word = self.room[self.pc + delta: self.pc + delta + 2]
        return struct.unpack('<H', word)[0]

    def get_data(self, delta=0, size=1):
        data = self.room[self.pc + delta: self.pc + size]
        return data

    def dump_text(self):
        text_program = self.program.filter(lambda _, e: e[0][0] == 'text')
        sorted_program_keys = sorted(text_program.keys())
        if len(sorted_program_keys) > 0:
            root = ET.Element('texts')
            root.set('room_id', str(self.id))
            root.set('base', hex(sorted_program_keys[0]))

            for key in sorted_program_keys:
                text = ET.SubElement(root, 'text')

                refs = ET.SubElement(text, 'refs')

                pointers = self.program._text_pointers[key]

                for pointer in pointers:
                    ref = ET.SubElement(refs, 'ref')
                    ref.text = hex(pointer)

                data = ET.SubElement(text, 'data')
                # if self.suffix == '_jp':
                #     data.text = bl_lookup_prefixed_chars(bytes(text_program[key][0][1]), self.table).replace('\\s', ' ')
                # else:
                data.text = self.table.to_text(bytes(text_program[key][0][1])).replace('\\s', ' ')

            return prettify(root)
        return None

    def _apply_patches(self, base, patches, text_data):
        patched_room = self.room[:base] + text_data

        for address, pointer in patches.items():
            patched_room[address] = pointer & 0xFF
            patched_room[address + 1] = (pointer >> 8) & 0xFF

        return patched_room

    def update_text(self, text_file):
        tree = ET.parse(text_file)
        texts = tree.getroot()

        base = int(texts.get('base'), 16)
        patches = {}

        text_data = b''
        for text in texts:
            refs = text.find('refs')

            for ref in refs:
                patches[int(ref.text, 16)] = base + len(text_data)

            data = text.find('data')
            encoded_text = self.table.to_bytes(data.text.replace(' ', r'\s'))
            # print('encoded', self.table.to_text(encoded_text).replace(r'\s', ' '))
            text_data += encoded_text

        return self._apply_patches(base, patches, text_data)
