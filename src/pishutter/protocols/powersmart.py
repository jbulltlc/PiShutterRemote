from dataclasses import dataclass
from enum import Enum

from pishutter.modulation.manchester import encode_powersmart_frame


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
        return encode_powersmart_frame(self.payload_for(command))