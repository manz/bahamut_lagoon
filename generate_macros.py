#!/usr/bin/env python3
"""
Generate a816 macro library for Bahamut Lagoon room opcodes
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Literal

from utils.vm.opcodes import ActorList, ConditionalJump, IfElseOpcode, Opcode, Opcode13, StateOpcode, TextOpcode
from utils.vm.opcodes_map import opcode_names, opcode_table


def get_opcode_size(opcode_num: int) -> int | Literal["variable"]:
    """Get the size of an opcode from the opcode table"""
    if opcode_num in opcode_table:
        opcode_obj = opcode_table[opcode_num]
        if isinstance(opcode_obj, (Opcode, TextOpcode)):
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


def with_docstring(macro: str, doc: str) -> str:
    """Put doc as the first line of the macro body, where a816 reads macro docstrings."""
    if not macro.startswith(".macro"):
        return macro
    signature, body = macro.split("\n", 1)
    return f'{signature}\n    """{doc}"""\n{body}'


def generate_macro_library() -> str:
    """Generate the complete a816 macro library"""

    header = (
        '"""\n'
        "Bahamut Lagoon room script macro library.\n"
        "\n"
        "Generated from utils/vm/opcodes_map.py by generate_macros.py: edit the generator, not this file.\n"
        '"""\n\n\n'
    )

    # Generate macros for each opcode
    macros = []

    for opcode_num in sorted(opcode_names.keys()):
        name = opcode_names[opcode_num]
        size = get_opcode_size(opcode_num)

        # Clean up macro name (remove special chars, make valid identifier)
        macro_name = name.replace("?", "").replace("-", "_").replace(" ", "_")

        opcode_obj = opcode_table.get(opcode_num)
        if isinstance(opcode_obj, ConditionalJump):
            # Condition bytes, then the address taken when the condition holds
            conditions = [f"param{i + 1}" for i in range(opcode_obj.operands)]
            macro = f""".macro {macro_name}({", ".join([*conditions, "address"])}) {{
    .db 0x{opcode_num:02X}, {", ".join(conditions)}
    .dw address
}}
"""
        elif isinstance(opcode_obj, Opcode13):
            # The actor; its motion steps follow as `.db`, ended by FF (or FE)
            macro = f""".macro {macro_name}(actor) {{
    .db 0x{opcode_num:02X}, actor
}}
"""
        elif isinstance(opcode_obj, ActorList):
            # The opcode; the actor ids follow as `.db`, ended by FF
            macro = f""".macro {macro_name}() {{
    .db 0x{opcode_num:02X}
}}
"""
        elif isinstance(opcode_obj, StateOpcode):
            # One flag: its word index (high five bits) and bit (low three)
            macro = f""".macro {macro_name}(flag) {{
    .db 0x{opcode_num:02X}, flag
}}
"""
        elif isinstance(opcode_obj, IfElseOpcode):
            # Two script addresses, one taken at random
            macro = f""".macro {macro_name}(first, second) {{
    .db 0x{opcode_num:02X}
    .dw first
    .dw second
}}
"""
        elif size == 1:
            # No parameters
            macro = f""".macro {macro_name}() {{
    .db 0x{opcode_num:02X}
}}
"""
        elif size == 2:
            # One parameter
            macro = f""".macro {macro_name}(param1) {{
    .db 0x{opcode_num:02X}, param1
}}
"""
        elif size == 3:
            # Two parameters or address
            if opcode_num in [0x00, 0x05]:  # Jump opcodes
                macro = f""".macro {macro_name}(address) {{
    .db 0x{opcode_num:02X}
    .dw address
}}
"""
            elif opcode_num in [0x37]:  # Text display
                macro = f""".macro {macro_name}(text_address) {{
    .db 0x{opcode_num:02X}
    .dw text_address
}}
"""
            else:
                macro = f""".macro {macro_name}(param1, param2) {{
    .db 0x{opcode_num:02X}, param1, param2
}}
"""
        elif size == 4:
            # Three parameters
            macro = f""".macro {macro_name}(param1, param2, param3) {{
    .db 0x{opcode_num:02X}, param1, param2, param3
}}
"""
        elif size == 5:
            # Four parameters
            macro = f""".macro {macro_name}(param1, param2, param3, param4) {{
    .db 0x{opcode_num:02X}, param1, param2, param3, param4
}}
"""
        elif isinstance(size, str):  # "variable"
            # Variable size opcodes (choices, etc.)
            if opcode_num == 0x08:  # yes_no
                macro = f""".macro {macro_name}(text_addr, yes_addr, no_addr) {{
    .db 0x{opcode_num:02X}
    .dw text_addr
    .dw yes_addr
    .dw no_addr
}}
"""
            elif opcode_num == 0x09:  # multiple_choice
                macro = f""".macro {macro_name}(text_addr, choice1, choice2, choice3) {{
    .db 0x{opcode_num:02X}
    .dw text_addr
    .dw choice1
    .dw choice2
    .dw choice3
}}
"""
            else:
                macro = f"""; {macro_name} - variable size opcode 0x{opcode_num:02X}
; Manual implementation required
"""
        else:
            # Handle larger fixed sizes
            params = ", ".join([f"param{i + 1}" for i in range(size - 1)])
            param_bytes = ", ".join([f"param{i + 1}" for i in range(size - 1)])
            macro = f""".macro {macro_name}({params}) {{
    .db 0x{opcode_num:02X}, {param_bytes}
}}
"""

        macros.append(with_docstring(macro, f"Room opcode 0x{opcode_num:02X}: {name}."))

    return header + "\n".join(macros)


def main() -> None:
    """Generate and save the macro library"""
    macros = generate_macro_library()

    output_file = "src/room_macros.s"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        f.write(macros)
    # The a816 formatter wraps long macro signatures the way `make check` expects
    subprocess.run([str(Path(sys.executable).parent / "a816"), "format", output_file], check=True)

    print(f"Generated room macro library: {output_file}")
    print(f"Total opcodes: {len(opcode_names)}")


if __name__ == "__main__":
    main()
