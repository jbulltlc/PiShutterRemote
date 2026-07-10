from fastapi import FastAPI, HTTPException

from pishutter.cc1101.driver import CC1101ShutterTransmitter
from pishutter.controller import PiShutterController
from pishutter.protocols.shutters import SHUTTERS

def create_controller() -> PiShutterController:
    return PiShutterController(
        transmitter=CC1101ShutterTransmitter(),
        state_path=STATE_PATH,
    )

STATE_PATH = "/config/pishutter/state.json"

app = FastAPI(title="PiShutterRemote")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/blinds")
def list_blinds():
    return {
        key: {
            "name": remote.name,
        }
        for key, remote in SHUTTERS.items()
    }


@app.get("/blinds/{blind_key}")
def get_blind(blind_key: str):
    try:
        with create_controller() as controller:
            blind = controller.get_blind(blind_key)
            return {
                "key": blind.key,
                "name": blind.name,
                "state": blind.state,
            }
    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex))


@app.post("/blinds/{blind_key}/up")
def blind_up(blind_key: str):
    return _send(blind_key, "up")


@app.post("/blinds/{blind_key}/down")
def blind_down(blind_key: str):
    return _send(blind_key, "down")


@app.post("/blinds/{blind_key}/stop")
def blind_stop(blind_key: str):
    return _send(blind_key, "stop")


@app.post("/blinds/{blind_key}/position/{position}")
def blind_position(blind_key: str, position: int):
    try:
        with create_controller() as controller:
            blind = controller.get_blind(blind_key)
            blind.set_position(position)
            return {"ok": True, "blind": blind_key, "position": blind.position}
    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex))


@app.post("/blinds/{blind_key}/calibrate/closed")
def calibrate_closed(blind_key: str):
    try:
        with create_controller() as controller:
            blind = controller.get_blind(blind_key)
            blind.calibrate_closed()
            return {"ok": True, "blind": blind_key, "position": blind.position}
    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex))


@app.post("/blinds/{blind_key}/calibrate/open")
def calibrate_open(blind_key: str):
    try:
        with create_controller() as controller:
            blind = controller.get_blind(blind_key)
            blind.calibrate_open()
            return {"ok": True, "blind": blind_key, "position": blind.position}
    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex))


def _send(blind_key: str, command: str):
    try:
        with create_controller() as controller:
            blind = controller.get_blind(blind_key)
            blind.send(command)
            return {"ok": True, "blind": blind_key, "command": command}
    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex))