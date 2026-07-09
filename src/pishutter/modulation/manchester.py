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

def encode_manchester_bits(payload_hex: str) -> str:
    """
    Standard Manchester chip mapping used by this protocol:
      data bit 1 -> 10
      data bit 0 -> 01
    """
    data = bytes.fromhex(payload_hex)
    chips: list[str] = []

    for byte in data:
        for bit_index in range(7, -1, -1):
            bit = (byte >> bit_index) & 1
            chips.append("10" if bit else "01")

    return "".join(chips)


def encode_powersmart_frame(payload_hex: str) -> str:
    """
    Generate the validated PowerSmart raw OOK frame.

    This deliberately matches the captured remote waveform:
      leading 1 + first 122 Manchester chips + trailer 101
    """
    manchester = encode_manchester_bits(payload_hex)
    return "1" + manchester[:122] + "101"