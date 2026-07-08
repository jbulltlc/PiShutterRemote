import time

from pishutter.cc1101.radio import CC1101Radio
from pishutter.cc1101 import registers as r


FIFO_SIZE = 64

POWERSMART_OOK_REGS = {
    r.IOCFG2: 0x06,
    r.IOCFG0: 0x06,
    r.PKTLEN: 0xFF,
    r.PKTCTRL1: 0x00,
    r.PKTCTRL0: 0x02,  # infinite packet length mode
    r.FSCTRL1: 0x06,
    r.FREQ2: 0x10,
    r.FREQ1: 0xAB,
    r.FREQ0: 0x92,
    r.MDMCFG4: 0x87,
    r.MDMCFG3: 0x66,
    r.MDMCFG2: 0x30,  # ASK/OOK, no sync
    r.MDMCFG1: 0x22,
    r.MDMCFG0: 0xF8,
    r.DEVIATN: 0x00,
    r.MCSM1: 0x00,
    r.MCSM0: 0x18,
    r.FOCCFG: 0x16,
    r.BSCFG: 0x6C,
    r.AGCCTRL2: 0x43,
    r.AGCCTRL1: 0x40,
    r.AGCCTRL0: 0x91,
    r.FREND1: 0x56,
    r.FREND0: 0x11,
    r.FSCAL3: 0xE9,
    r.FSCAL2: 0x2A,
    r.FSCAL1: 0x00,
    r.FSCAL0: 0x1F,
    r.TEST2: 0x81,
    r.TEST1: 0x35,
    r.TEST0: 0x09,
}


class CC1101OOKTransmitter:
    def __init__(self, radio: CC1101Radio):
        self.radio = radio

    def configure(self) -> None:
        self.radio.reset()

        for address, value in POWERSMART_OOK_REGS.items():
            self.radio.write_reg(address, value)

        self.radio.write_burst(r.PATABLE, [0x00, 0xC0])

    def _tx_fifo_count(self) -> int:
        return self.radio.read_status(r.TXBYTES) & 0x7F

    def transmit(self, data: bytes) -> None:
        self.radio.strobe(r.SIDLE)
        self.radio.strobe(r.SFTX)
        time.sleep(0.01)

        offset = 0

        preload = data[:60]
        self.radio.write_burst(r.FIFO, preload)
        offset += len(preload)

        self.radio.strobe(r.STX)

        while offset < len(data):
            count = self._tx_fifo_count()

            if count < 32:
                space = FIFO_SIZE - count
                chunk_size = min(space, 32, len(data) - offset)
                chunk = data[offset:offset + chunk_size]

                self.radio.write_burst(r.FIFO, chunk)
                offset += len(chunk)

            time.sleep(0.01)

        while self._tx_fifo_count() > 0:
            time.sleep(0.01)

        time.sleep(0.02)
        self.radio.strobe(r.SIDLE)