def encode_bits_from_hex(payload_hex: str) -> str:
    data = bytes.fromhex(payload_hex)
    chips = []

    for byte in data:
        for bit_index in range(7, -1, -1):
            bit = (byte >> bit_index) & 1
            chips.append("10" if bit else "01")

    return "".join(chips)


def encode_powersmart_raw_frame(payload_hex: str) -> str:
    """
    Generate the exact raw OOK frame observed from the PowerSmart remote.

    Validated against captured UP/STOP/DOWN frames:
      raw_frame = leading '1' + first 122 Manchester chips + trailer '101'
    """
    manchester = encode_bits_from_hex(payload_hex)
    return "1" + manchester[:122] + "101"