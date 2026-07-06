def encode_bits_from_hex(payload_hex: str) -> str:
    """
    Encode payload as PowerSmart/Manchester chips.

    Mapping based on our successful captures:
      data bit 1 -> 10
      data bit 0 -> 01
    """
    data = bytes.fromhex(payload_hex)
    chips = []

    for byte in data:
        for bit_index in range(7, -1, -1):
            bit = (byte >> bit_index) & 1
            chips.append("10" if bit else "01")

    return "".join(chips)