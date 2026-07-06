#!/usr/bin/env python3

import time
import spidev

SRES = 0x30
STX = 0x35
SIDLE = 0x36
SFTX = 0x3B

TXFIFO = 0x3F
PATABLE = 0x3E

WRITE_BURST = 0x40
READ_BURST = 0xC0

TXBYTES = 0x3A

RAW_UP = (
    "1101010101010011010010101010110011001101010100101100110011001010"
    "11001100110011001011010101010011001100101010110100110011001101"
)

CHIP_US = 225
GAP_SAMPLES = 19150
SAMPLE_RATE = 1_792_000

# Convert your measured URH gap to Manchester/OOK chips
GAP_US = GAP_SAMPLES / SAMPLE_RATE * 1_000_000
GAP_CHIPS = round(GAP_US / CHIP_US)

REPEATS = 8

REGS = {
    0x00: 0x06,
    0x02: 0x06,

    0x06: 0xFF,
    0x07: 0x00,

    # Infinite packet length mode, no CRC, no whitening
    0x08: 0x02,

    0x0B: 0x06,

    # 433.425 MHz
    0x0D: 0x10,
    0x0E: 0xAB,
    0x0F: 0x92,

    # ~4438 chips/sec
    0x10: 0x87,
    0x11: 0x66,

    # ASK/OOK, no sync
    0x12: 0x30,

    0x13: 0x22,
    0x14: 0xF8,
    0x15: 0x00,

    0x17: 0x00,
    0x18: 0x18,

    0x19: 0x16,
    0x1A: 0x6C,
    0x1B: 0x43,
    0x1C: 0x40,
    0x1D: 0x91,

    0x21: 0x56,
    0x22: 0x11,

    0x23: 0xE9,
    0x24: 0x2A,
    0x25: 0x00,
    0x26: 0x1F,

    0x2C: 0x81,
    0x2D: 0x35,
    0x2E: 0x09,
}


def strobe(spi, cmd):
    return spi.xfer2([cmd])[0]


def write_reg(spi, addr, value):
    spi.xfer2([addr, value])


def write_burst(spi, addr, values):
    spi.xfer2([addr | WRITE_BURST] + list(values))


def read_status(spi, addr):
    return spi.xfer2([addr | READ_BURST, 0x00])[1]


def tx_fifo_count(spi):
    value = read_status(spi, TXBYTES)
    return value & 0x7F


def pack_bits(bits: str) -> bytes:
    while len(bits) % 8 != 0:
        bits += "0"

    out = []
    for i in range(0, len(bits), 8):
        out.append(int(bits[i:i + 8], 2))
    return bytes(out)


def build_stream() -> bytes:
    gap = "0" * GAP_CHIPS

    # One extra leading chip compensates for the CC1101 startup/first-chip loss.
    bits = "1"

    for i in range(REPEATS):
        bits += RAW_UP
        if i != REPEATS - 1:
            bits += gap

    print(f"Frame bits: {len(RAW_UP)}")
    print(f"Gap chips: {GAP_CHIPS}")
    print(f"Total chips: {len(bits)}")

    return pack_bits(bits)


def configure(spi):
    strobe(spi, SRES)
    time.sleep(0.1)

    for addr, value in REGS.items():
        write_reg(spi, addr, value)

    write_burst(spi, PATABLE, [0x00, 0xC0])


def transmit_stream(spi, data: bytes):
    strobe(spi, SIDLE)
    strobe(spi, SFTX)
    time.sleep(0.01)

    offset = 0

    # Preload FIFO
    first = data[:60]
    write_burst(spi, TXFIFO, first)
    offset += len(first)

    print(f"Preloaded {len(first)} bytes")
    print("STX")
    strobe(spi, STX)

    while offset < len(data):
        count = tx_fifo_count(spi)

        if count < 32:
            space = 64 - count
            chunk = data[offset:offset + min(space, 32)]
            write_burst(spi, TXFIFO, chunk)
            offset += len(chunk)
            print(f"Wrote {len(chunk)} bytes, offset {offset}/{len(data)}, fifo {count}")

        time.sleep(0.01)

    print("Waiting for FIFO to drain...")
    while tx_fifo_count(spi) > 0:
        time.sleep(0.01)

    time.sleep(0.02)
    strobe(spi, SIDLE)


def main():
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 500_000
    spi.mode = 0

    try:
        configure(spi)
        data = build_stream()

        print(f"TX bytes: {len(data)}")
        print(f"Data preview: {data[:16].hex()}")

        transmit_stream(spi, data)

        print("Done")

    finally:
        strobe(spi, SIDLE)
        spi.close()


if __name__ == "__main__":
    main()