#!/usr/bin/env python3

import argparse
import time

import spidev

from pishutter.protocols.powersmart import Command
from pishutter.protocols.shutters import SHUTTERS

SRES = 0x30
STX = 0x35
SIDLE = 0x36
SFTX = 0x3B

TXFIFO = 0x3F
PATABLE = 0x3E
TXBYTES = 0x3A

WRITE_BURST = 0x40
READ_BURST = 0xC0

CHIP_US = 225
SAMPLE_RATE = 1_792_000
GAP_SAMPLES = 19_150
GAP_CHIPS = round((GAP_SAMPLES / SAMPLE_RATE * 1_000_000) / CHIP_US)

REPEATS = 8
FIFO_SIZE = 64


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
    0x12: 0x30,  # ASK/OOK, no sync
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


def strobe(spi, command: int) -> int:
    return spi.xfer2([command])[0]


def write_reg(spi, address: int, value: int) -> None:
    spi.xfer2([address, value])


def write_burst(spi, address: int, values: bytes | list[int]) -> None:
    spi.xfer2([address | WRITE_BURST] + list(values))


def read_status(spi, address: int) -> int:
    return spi.xfer2([address | READ_BURST, 0x00])[1]


def tx_fifo_count(spi) -> int:
    return read_status(spi, TXBYTES) & 0x7F


def pack_bits(bits: str) -> bytes:
    padding = (-len(bits)) % 8
    bits += "0" * padding

    return bytes(
        int(bits[index:index + 8], 2)
        for index in range(0, len(bits), 8)
    )


def build_stream(remote, command: Command) -> bytes:
    frame = remote.raw_frame_for(command)
    gap = "0" * GAP_CHIPS

    bits = "1"  # startup compensation chip from the working POC

    for index in range(REPEATS):
        bits += frame
        if index != REPEATS - 1:
            bits += gap

    payload = remote.payload_for(command)

    print(f"Shutter:     {remote.name}")
    print(f"Command:     {command.value}")
    print(f"Payload:     {payload}")
    print(f"Frame chips: {len(frame)}")
    print(f"Gap chips:   {GAP_CHIPS}")
    print(f"Total chips: {len(bits)}")

    return pack_bits(bits)


def configure_radio(spi) -> None:
    strobe(spi, SRES)
    time.sleep(0.1)

    for address, value in REGS.items():
        write_reg(spi, address, value)

    write_burst(spi, PATABLE, [0x00, 0xC0])


def transmit_stream(spi, data: bytes) -> None:
    strobe(spi, SIDLE)
    strobe(spi, SFTX)
    time.sleep(0.01)

    offset = 0

    preload = data[:60]
    write_burst(spi, TXFIFO, preload)
    offset += len(preload)

    strobe(spi, STX)

    while offset < len(data):
        count = tx_fifo_count(spi)

        if count < 32:
            space = FIFO_SIZE - count
            chunk_size = min(space, 32, len(data) - offset)
            chunk = data[offset:offset + chunk_size]

            write_burst(spi, TXFIFO, chunk)
            offset += len(chunk)

        time.sleep(0.01)

    while tx_fifo_count(spi) > 0:
        time.sleep(0.01)

    time.sleep(0.02)
    strobe(spi, SIDLE)


def open_spi():
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 500_000
    spi.mode = 0
    return spi


def parse_args():
    parser = argparse.ArgumentParser(
        description="Transmit a PowerSmart shutter command via CC1101."
    )

    parser.add_argument(
        "shutter",
        choices=sorted(SHUTTERS.keys()),
        help="Shutter name",
    )

    parser.add_argument(
        "command",
        choices=[command.value for command in Command],
        help="Command to transmit",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    remote = SHUTTERS[args.shutter]
    command = Command(args.command)

    spi = open_spi()

    try:
        configure_radio(spi)
        data = build_stream(remote, command)

        print(f"TX bytes:    {len(data)}")

        transmit_stream(spi, data)

        print("Done")

    finally:
        strobe(spi, SIDLE)
        spi.close()


if __name__ == "__main__":
    main()