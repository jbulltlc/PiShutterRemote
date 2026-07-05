import time
import spidev

from . import registers as r


class CC1101Radio:
    def __init__(self, bus: int = 0, device: int = 0, speed_hz: int = 500_000, debug: bool = False):
        self.bus = bus
        self.device = device
        self.speed_hz = speed_hz
        self.debug = debug
        self.spi = spidev.SpiDev()

    def open(self) -> None:
        self.spi.open(self.bus, self.device)
        self.spi.max_speed_hz = self.speed_hz
        self.spi.mode = 0
        time.sleep(0.05)

    def close(self) -> None:
        self.spi.close()

    def _log(self, message: str) -> None:
        if self.debug:
            print(message)

    def strobe(self, command: int) -> int:
        result = self.spi.xfer2([command])[0]
        self._log(f"STROBE 0x{command:02X} -> 0x{result:02X}")
        return result

    def reset(self) -> None:
        self._log("RESET")
        self.strobe(r.SRES)
        time.sleep(0.1)

    def write_reg(self, address: int, value: int) -> None:
        self.spi.xfer2([address, value])
        self._log(f"WRITE 0x{address:02X} = 0x{value:02X}")

    def read_reg(self, address: int) -> int:
        value = self.spi.xfer2([address | r.READ_SINGLE, 0x00])[1]
        self._log(f"READ 0x{address:02X} -> 0x{value:02X}")
        return value

    def read_status(self, address: int) -> int:
        value = self.spi.xfer2([address | r.READ_BURST, 0x00])[1]
        self._log(f"STATUS 0x{address:02X} -> 0x{value:02X}")
        return value

    def write_burst(self, address: int, values) -> None:
        values = list(values)
        self.spi.xfer2([address | r.WRITE_BURST] + values)
        self._log("BURST WRITE 0x%02X: %s" % (address, " ".join(f"{v:02X}" for v in values)))

    def read_burst(self, address: int, length: int) -> list[int]:
        values = self.spi.xfer2([address | r.READ_BURST] + [0x00] * length)[1:]
        self._log("BURST READ 0x%02X: %s" % (address, " ".join(f"{v:02X}" for v in values)))
        return values

    def check_connection(self) -> tuple[int, int]:
        return self.read_status(r.PARTNUM), self.read_status(r.VERSION)