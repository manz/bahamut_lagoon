"""Apply IPS patches."""


def apply_ips(rom: bytes, patch: bytes) -> bytes:
    """Return rom with the IPS patch applied, growing it when records write past its end."""
    if not (patch.startswith(b"PATCH") and patch.endswith(b"EOF")):
        raise ValueError("not an IPS patch")
    out = bytearray(rom)
    i = 5
    while patch[i : i + 3] != b"EOF":
        offset = int.from_bytes(patch[i : i + 3], "big")
        size = int.from_bytes(patch[i + 3 : i + 5], "big")
        i += 5
        if size == 0:  # RLE record: run length, then the byte to repeat
            data = patch[i + 2 : i + 3] * int.from_bytes(patch[i : i + 2], "big")
            i += 3
        else:
            data = patch[i : i + size]
            i += size
        if offset + len(data) > len(out):
            out.extend(bytes(offset + len(data) - len(out)))
        out[offset : offset + len(data)] = data
    return bytes(out)
