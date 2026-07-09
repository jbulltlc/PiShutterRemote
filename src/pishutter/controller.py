import time

from pishutter.cc1101.radio import CC1101Radio
from pishutter.cc1101.transmitter import CC1101OOKTransmitter
from pishutter.modulation.stream import build_repeated_stream_bytes
from pishutter.protocols.powersmart import Command, PowerSmartRemote
from pishutter.protocols.shutters import SHUTTERS
from pishutter.state import StateStore
from pathlib import Path

class PiShutterController:
    def __init__(self, state_store: StateStore | None = None, state_path: str | None = None):
        self.radio = CC1101Radio()
        self.transmitter = CC1101OOKTransmitter(self.radio)

        if state_store is not None:
            self.state_store = state_store
        elif state_path is not None:
            self.state_store = StateStore(Path(state_path))
        else:
            self.state_store = StateStore()

class PowerSmartBlind:
    def __init__(
        self,
        key: str,
        remote: PowerSmartRemote,
        controller: "PiShutterController",
    ):
        self.key = key
        self.remote = remote
        self.controller = controller

    @property
    def name(self) -> str:
        return self.remote.name

    @property
    def state(self) -> dict:
        return self.controller.state_store.get_blind_state(self.key)

    @property
    def position(self) -> int:
        return int(self.state["position"])

    def send(self, command: Command | str) -> None:
        self.controller.send(self.key, command)

    def up(self) -> None:
        self.send(Command.UP)

    def stop(self) -> None:
        self.send(Command.STOP)

    def down(self) -> None:
        self.send(Command.DOWN)

    def configure(
        self,
        open_time_seconds: float | None = None,
        close_time_seconds: float | None = None,
        safety_buffer_seconds: float | None = None,
        position: int | None = None,
    ) -> None:
        updates = {}

        if open_time_seconds is not None:
            updates["open_time_seconds"] = float(open_time_seconds)

        if close_time_seconds is not None:
            updates["close_time_seconds"] = float(close_time_seconds)

        if safety_buffer_seconds is not None:
            updates["safety_buffer_seconds"] = float(safety_buffer_seconds)

        if position is not None:
            updates["position"] = max(0, min(100, int(position)))

        self.controller.state_store.update_blind_state(self.key, **updates)

    def set_position(self, target: int) -> None:
        target = max(0, min(100, int(target)))
        current = self.position

        if target == current:
            return

        if target == 0:
            self.calibrate_closed()
            return

        if target == 100:
            self.calibrate_open()
            return

        delta = target - current

        if delta > 0:
            travel_time = self.state["open_time_seconds"] * (delta / 100)
            self.up()
        else:
            travel_time = self.state["close_time_seconds"] * (abs(delta) / 100)
            self.down()

        time.sleep(travel_time)
        self.stop()

        self.controller.state_store.update_blind_state(
            self.key,
            position=target,
        )

    def calibrate_closed(self) -> None:
        self.down()
        time.sleep(
            self.state["close_time_seconds"]
            + self.state["safety_buffer_seconds"]
        )
        self.controller.state_store.update_blind_state(self.key, position=0)

    def calibrate_open(self) -> None:
        self.up()
        time.sleep(
            self.state["open_time_seconds"]
            + self.state["safety_buffer_seconds"]
        )
        self.controller.state_store.update_blind_state(self.key, position=100)


class PiShutterController:
    def __init__(self, state_store: StateStore | None = None):
        self.radio = CC1101Radio()
        self.transmitter = CC1101OOKTransmitter(self.radio)
        self.state_store = state_store or StateStore()

        self.blinds = {
            key: PowerSmartBlind(key, remote, self)
            for key, remote in SHUTTERS.items()
        }

    def __enter__(self):
        self.radio.open()
        self.transmitter.configure()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.radio.close()

    def get_blind(self, key: str) -> PowerSmartBlind:
        if key not in self.blinds:
            raise ValueError(f"Unknown blind: {key}")
        return self.blinds[key]

    def send(self, shutter_key: str, command: Command | str) -> None:
        if isinstance(command, str):
            command = Command(command)

        blind = self.get_blind(shutter_key)
        frame = blind.remote.raw_frame_for(command)
        data = build_repeated_stream_bytes(frame)

        self.transmitter.transmit(data)

    def up(self, shutter_key: str) -> None:
        self.get_blind(shutter_key).up()

    def stop(self, shutter_key: str) -> None:
        self.get_blind(shutter_key).stop()

    def down(self, shutter_key: str) -> None:
        self.get_blind(shutter_key).down()

    def set_position(self, shutter_key: str, position: int) -> None:
        self.get_blind(shutter_key).set_position(position)