from dataclasses import dataclass
from enum import Enum

from pishutter.modulation.manchester import encode_bits_from_hex


class Command(str, Enum):
    UP = "up"
    STOP = "stop"
    DOWN = "down"


@dataclass(frozen=True)
class PowerSmartRemote:
    name: str
    up: str
    stop: str
    down: str

    def payload_for(self, command: Command) -> str:
        if command == Command.UP:
            return self.up
        if command == Command.STOP:
            return self.stop
        if command == Command.DOWN:
            return self.down
        raise ValueError(f"Unsupported command: {command}")

    def raw_frame_for(self, command: Command) -> str:
        if command == Command.UP:
            return (
                "1101010101010011010010101010110011001101010100101100110011001010"
                "11001100110011001011010101010011001100101010110100110011001101"
            )

        if command == Command.STOP:
            return (
                "11010101010100110100101010101100110011010101001101001100110010101"
                "1001100110011001011010101010011001100101010110010110011001101"
            )

        if command == Command.DOWN:
            return (
                "11010101010100110010101010101100110011010101001101001100110010101"
                "1001100110011001101010101010011001100101010110010110011001101"
            )

        raise NotImplementedError(
            "Only UP raw frame has been validated so far."
        )


DEFAULT_REMOTE = PowerSmartRemote(
    name="test_shutter",
    up="fd82bca8aa7d4351",
    stop="fd82bda8aa7d4251",
    down="fd02bda8aafd4251",
)