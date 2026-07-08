#!/usr/bin/env python3

import argparse
import time

from pishutter.protocols.powersmart import Command
from pishutter.protocols.shutters import SHUTTERS

CHIP_US = 225
SAMPLE_RATE = 1_792_000
GAP_SAMPLES = 19_150
GAP_CHIPS = round((GAP_SAMPLES / SAMPLE_RATE * 1_000_000) / CHIP_US)

REPEATS = 8
FIFO_SIZE = 64

from pishutter.cc1101.radio import CC1101Radio
from pishutter.cc1101.transmitter import CC1101OOKTransmitter

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

    radio = CC1101Radio()

    try:
        radio.open()

        transmitter = CC1101OOKTransmitter(radio)
        transmitter.configure()

        data = build_stream(remote, command)

        print(f"TX bytes:    {len(data)}")

        transmitter.transmit(data)

        print("Done")

    finally:
        radio.close()


if __name__ == "__main__":
    main()