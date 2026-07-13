from __future__ import annotations

import threading

from pishutter.cc1101.radio import CC1101Radio
from pishutter.cc1101.transmitter import CC1101OOKTransmitter
from pishutter.modulation.stream import build_repeated_stream_bytes
from pishutter.protocols.powersmart import Command, PowerSmartRemote


class CC1101ShutterTransmitter:
    def __init__(
        self,
        bus: int = 0,
        device: int = 0,
        speed_hz: int = 500_000,
    ) -> None:
        self._radio = CC1101Radio(
            bus=bus,
            device=device,
            speed_hz=speed_hz,
        )
        self._transmitter = CC1101OOKTransmitter(self._radio)
        self._is_open = False

        # Only one thread may access the CC1101 at a time.
        self._lock = threading.Lock()

    def open(self) -> None:
        with self._lock:
            if self._is_open:
                return

            self._radio.open()
            self._transmitter.configure()
            self._is_open = True

    def close(self) -> None:
        with self._lock:
            if not self._is_open:
                return

            self._radio.close()
            self._is_open = False

    def send(
        self,
        remote: PowerSmartRemote,
        command: Command,
    ) -> None:
        frame = remote.raw_frame_for(command)
        data = build_repeated_stream_bytes(frame)

        with self._lock:
            if not self._is_open:
                raise RuntimeError("Transmitter is not open")

            self._transmitter.transmit(data)