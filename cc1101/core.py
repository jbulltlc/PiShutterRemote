#!/usr/bin/env python3

import time
import spidev


# SPI command masks
WRITE_BURST = 0x40
READ_SINGLE = 0x80
READ_BURST = 0xC0

# CC1101 command strobes
SRES  = 0x30
SFSTXON = 0x31
SXOFF = 0x32
SCAL  = 0x33
SRX   = 0x34
STX   = 0x35
SIDLE = 0x36
SAFC  = 0x37
SWOR  = 0x38
SPWD  = 0x39
SFRX  = 0x3A
SFTX  = 0x3B
SWORRST = 0x3C
SNOP  = 0x3D

# Status registers
PARTNUM = 0x30
VERSION = 0x31
MARCSTATE = 0x35
TXBYTES = 0x3A
RXBYTES = 0x3B


class CC1101:
    def __init__(self, bus=0, device=0, speed_hz=500_000, debug=False):
        self.bus = bus
        self.device = device
        self.speed_hz = speed_hz
        self.debug = debug
        self.spi = spidev.SpiDev()

    def open(self):
        self.spi.open(self.bus, self.device)
        self.spi.max_speed_hz = self.speed_hz
        self.spi.mode = 0
        time.sleep(0.05)

    def close(self):
        self.spi.close()

    def _log(self, message):
        if self.debug:
            print(message)

    def strobe(self, command):
        result = self.spi.xfer2([command])[0]
        self._log(f"STROBE 0x{command:02X} -> 0x{result:02X}")
        return result

    def reset(self):
        self._log("RESET")
        self.strobe(SRES)
        time.sleep(0.1)

    def write_reg(self, address, value):
        self.spi.xfer2([address, value])
        self._log(f"WRITE 0x{address:02X} = 0x{value:02X}")

    def read_reg(self, address):
        result = self.spi.xfer2([address | READ_SINGLE, 0x00])[1]
        self._log(f"READ 0x{address:02X} -> 0x{result:02X}")
        return result

    def read_status(self, address):
        result = self.spi.xfer2([address | READ_BURST, 0x00])[1]
        self._log(f"STATUS 0x{address:02X} -> 0x{result:02X}")
        return result

    def write_burst(self, address, values):
        values = list(values)
        self.spi.xfer2([address | WRITE_BURST] + values)
        self._log(
            f"BURST WRITE 0x{address:02X}: "
            + " ".join(f"{v:02X}" for v in values)
        )

    def read_burst(self, address, length):
        result = self.spi.xfer2([address | READ_BURST] + [0x00] * length)[1:]
        self._log(
            f"BURST READ 0x{address:02X}: "
            + " ".join(f"{v:02X}" for v in result)
        )
        return result

    def check_connection(self):
        partnum = self.read_status(PARTNUM)
        version = self.read_status(VERSION)

        return {
            "partnum": partnum,
            "version": version,
            "ok": not (
                partnum in (0xFF, 0x00) and version in (0xFF, 0x00)
            ),
        }