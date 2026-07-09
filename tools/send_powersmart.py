#!/usr/bin/env python3

import argparse

from pishutter.controller import PiShutterController
from pishutter.protocols.powersmart import Command
from pishutter.protocols.shutters import SHUTTERS


def parse_args():
    parser = argparse.ArgumentParser(
        description="Control a PowerSmart shutter via CC1101."
    )

    parser.add_argument("shutter", choices=sorted(SHUTTERS.keys()))

    subcommands = parser.add_subparsers(dest="action", required=True)

    for command in Command:
        subcommands.add_parser(command.value)

    position_parser = subcommands.add_parser("position")
    position_parser.add_argument("value", type=int)

    subcommands.add_parser("calibrate-closed")
    subcommands.add_parser("calibrate-open")

    configure_parser = subcommands.add_parser("configure")
    configure_parser.add_argument("--open-time", type=float)
    configure_parser.add_argument("--close-time", type=float)
    configure_parser.add_argument("--buffer", type=float)
    configure_parser.add_argument("--position", type=int)

    subcommands.add_parser("status")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with PiShutterController() as controller:
        blind = controller.get_blind(args.shutter)

        if args.action in [command.value for command in Command]:
            blind.send(Command(args.action))

        elif args.action == "position":
            blind.set_position(args.value)

        elif args.action == "calibrate-closed":
            blind.calibrate_closed()

        elif args.action == "calibrate-open":
            blind.calibrate_open()

        elif args.action == "configure":
            blind.configure(
                open_time_seconds=args.open_time,
                close_time_seconds=args.close_time,
                safety_buffer_seconds=args.buffer,
                position=args.position,
            )

        elif args.action == "status":
            print(blind.state)

    print(f"Done: {args.shutter} {args.action}")


if __name__ == "__main__":
    main()