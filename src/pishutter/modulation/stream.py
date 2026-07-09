from pishutter.modulation.bits import pack_bits

CHIP_US = 225
SAMPLE_RATE = 1_792_000
GAP_SAMPLES = 19_150
GAP_CHIPS = round((GAP_SAMPLES / SAMPLE_RATE * 1_000_000) / CHIP_US)

REPEATS = 8


def build_repeated_stream(frame_bits: str, repeats: int = REPEATS) -> str:
    gap = "0" * GAP_CHIPS

    bits = "1"  # startup compensation chip from the working POC

    for index in range(repeats):
        bits += frame_bits
        if index != repeats - 1:
            bits += gap

    return bits


def build_repeated_stream_bytes(frame_bits: str, repeats: int = REPEATS) -> bytes:
    return pack_bits(build_repeated_stream(frame_bits, repeats))