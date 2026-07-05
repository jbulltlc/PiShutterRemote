#!/usr/bin/env python3

from pishutter.cc1101.radio import CC1101Radio


def main():
    radio = CC1101Radio(debug=True)

    try:
        radio.open()
        radio.reset()

        partnum, version = radio.check_connection()

        print()
        print(f"PARTNUM: 0x{partnum:02X}")
        print(f"VERSION: 0x{version:02X}")

        if version == 0x14:
            print("CC1101 connection looks good.")
        else:
            print("Unexpected response. Check wiring or module type.")

    finally:
        radio.close()


if __name__ == "__main__":
    main()