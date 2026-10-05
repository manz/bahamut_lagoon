"""
Expansion bank FE, a pool for new code.

The vanilla image is 3 MB (banks C0-EF); build.py's relocated rooms and strings use F0-F4, FC and FD, so FE is free.
"""


.pool expansion {
    range 0xFE0000 0xFEFFFF
    strategy order
}
