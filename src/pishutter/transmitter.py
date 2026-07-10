from typing import Protocol

from pishutter.protocols.powersmart import Command, PowerSmartRemote


class ShutterTransmitter(Protocol):
    def open(self) -> None:
        """Prepare the transmitter."""

    def close(self) -> None:
        """Release transmitter resources."""

    def send(
        self,
        remote: PowerSmartRemote,
        command: Command,
    ) -> None:
        """Transmit one command."""