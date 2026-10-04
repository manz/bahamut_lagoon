#!/usr/bin/env python3
"""
Generate a816 macro library for Bahamut Lagoon room opcodes
"""

import os
from utils.vm.opcodes_map import opcode_names, opcode_table

def get_opcode_size(opcode_num):
    """Get the size of an opcode from the opcode table"""
    if opcode_num in opcode_table:
        opcode_obj = opcode_table[opcode_num]
        if hasattr(opcode_obj, 'size'):
            return opcode_obj.size
        # For complex opcodes, return a default or check specific cases
        if opcode_num in [0x00, 0x01, 0x02, 0x03, 0x04, 0x05]:  # Jump opcodes
            return 3
        elif opcode_num in [0x08, 0x09]:  # Choice opcodes
            return "variable"
        elif opcode_num in [0x37, 0x7B]:  # Text opcodes
            return 3
        else:
            return 1
    return 1

def generate_macro_library():
    """Generate the complete a816 macro library"""
    
    header = '''; Bahamut Lagoon Room Script Macro Library
; Generated automatically from opcodes_map.py
; Use with a816 assembler

'''

    # Generate macros for each opcode
    macros = []
    
    for opcode_num in sorted(opcode_names.keys()):
        name = opcode_names[opcode_num]
        size = get_opcode_size(opcode_num)
        
        # Clean up macro name (remove special chars, make valid identifier)
        macro_name = name.replace('?', '').replace('-', '_').replace(' ', '_')
        
        if size == 1:
            # No parameters
            macro = f'''.macro {macro_name}() {{
    .db ${opcode_num:02X}
}}
'''
        elif size == 2:
            # One parameter
            macro = f'''.macro {macro_name}(param1) {{
    .db ${opcode_num:02X}, param1
}}
'''
        elif size == 3:
            # Two parameters or address
            if opcode_num in [0x00, 0x05]:  # Jump opcodes
                macro = f'''.macro {macro_name}(address) {{
    .db ${opcode_num:02X}
    .dw address
}}
'''
            elif opcode_num in [0x37]:  # Text display
                macro = f'''.macro {macro_name}(text_address) {{
    .db ${opcode_num:02X}
    .dw text_address
}}
'''
            else:
                macro = f'''.macro {macro_name}(param1, param2) {{
    .db ${opcode_num:02X}, param1, param2
}}
'''
        elif size == 4:
            # Three parameters
            macro = f'''.macro {macro_name}(param1, param2, param3) {{
    .db ${opcode_num:02X}, param1, param2, param3
}}
'''
        elif size == 5:
            # Four parameters
            macro = f'''.macro {macro_name}(param1, param2, param3, param4) {{
    .db ${opcode_num:02X}, param1, param2, param3, param4
}}
'''
        elif size == "variable":
            # Variable size opcodes (choices, etc.)
            if opcode_num == 0x08:  # yes_no
                macro = f'''.macro {macro_name}(text_addr, yes_addr, no_addr) {{
    .db ${opcode_num:02X}
    .dw text_addr
    .dw yes_addr  
    .dw no_addr
}}
'''
            elif opcode_num == 0x09:  # multiple_choice
                macro = f'''.macro {macro_name}(text_addr, choice1, choice2, choice3, choice4) {{
    .db ${opcode_num:02X}
    .dw text_addr
    .dw choice1
    .dw choice2  
    .dw choice3
    .dw choice4
}}
'''
            else:
                macro = f'''; {macro_name} - variable size opcode ${opcode_num:02X}
; Manual implementation required
'''
        else:
            # Handle larger fixed sizes
            params = ", ".join([f"param{i+1}" for i in range(size-1)])
            param_bytes = ", ".join([f"param{i+1}" for i in range(size-1)])
            macro = f'''.macro {macro_name}({params}) {{
    .db ${opcode_num:02X}, {param_bytes}
}}
'''
        
        macros.append(f'; ${opcode_num:02X}: {name}')
        macros.append(macro)
    
    return header + '\n'.join(macros)

def main():
    """Generate and save the macro library"""
    macros = generate_macro_library()
    
    output_file = "src/room_macros.s"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(macros)
    
    print(f"Generated room macro library: {output_file}")
    print(f"Total opcodes: {len(opcode_names)}")

if __name__ == "__main__":
    main()