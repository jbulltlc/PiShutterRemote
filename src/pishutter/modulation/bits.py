def pack_bits(bits: str) -> bytes:
    padding = (-len(bits)) % 8
    bits += "0" * padding

    return bytes(
        int(bits[index:index + 8], 2)
        for index in range(0, len(bits), 8)
    )