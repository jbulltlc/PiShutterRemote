#!/usr/bin/env python3

import argparse
import time
import spidev

from pishutter.protocols.powersmart import Command, DEFAULT_REMOTE

SRES = 0x30
STX = 0x35
SIDLE = 0x36
SFTX = 0x3B

TXFIFO = 0x3F
PATABLE = 0x3E

WRITE_BURST = 0x40
READ_BURST = 0xC0

TXBYTES = 0x3A

CHIP_US = 225
GAP_SAMPLES = 19150
SAMPLE_RATE = 1_792_000
GAP_US = GAP_SAMPLES / SAMPLE_RATE * 1_000_000
GAP_CHIPS = round(GAP_US / CHIP_US)

REPEATS = 8

REGS = {
    0x00: 0x06,
    0x02: 0x06,

    0x06: 0xFF,
    0x07: 0x00,
    0x08: 0x02,  # infinite packet length mode

    0x0B: 0x06,

    0x0D: 0x10,
    0x0E: 0xAB,
    0x0F: 0x92,

    0x10: 0x87,
    0x11: 0x66,
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
    return read_status(spi, TXBYTES) & 0x7F


def pack_bits(bits: str) -> bytes:
    while len(bits) % 8 != 0:
        bits += "0"

    return bytes(
        int(bits[i:i + 8], 2)
        for i in range(0, len(bits), 8)
    )


def build_stream(command: Command) -> bytes:
    frame = DEFAULT_REMOTE.raw_frame_for(command)
    gap = "0" * GAP_CHIPS

    # Startup compensation chip. This preserved the behaviour of the
    # successful continuous_tx_poc.py script.
    bits = "1"

    for i in range(REPEATS):
        bits += frame
        if i != REPEATS - 1:
            bits += gap

    print(f"Command: {command.value}")
    print(f"Payload: {DEFAULT_REMOTE.payload_for(command)}")
    print(f"Frame chips: {len(frame)}")
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

    first = data[:60]
    write_burst(spi, TXFIFO, first)
    offset += len(first)

    strobe(spi, STX)

    while offset < len(data):
        count = tx_fifo_count(spi)

        if count < 32:
            space = 64 - count
            chunk = data[offset:offset + min(space, 32)]
            write_burst(spi, TXFIFO, chunk)
            offset += len(chunk)

        time.sleep(0.01)

    while tx_fifo_count(spi) > 0:
        time.sleep(0.01)

    time.sleep(0.02)
    strobe(spi, SIDLE)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[c.value for c in Command],
        help="Command to transmit",
    )
    args = parser.parse_args()

    command = Command(args.command)

    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 500_000
    spi.mode = 0

    try:
        configure(spi)
        data = build_stream(command)
        print(f"TX bytes: {len(data)}")
        transmit_stream(spi, data)
        print("Done")

    finally:
        strobe(spi, SIDLE)
        spi.close()


if __name__ == "__main__":
    main()