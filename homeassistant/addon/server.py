from __future__ import annotations

from contextlib import asynccontextmanager
import threading

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from pishutter.cc1101.driver import CC1101ShutterTransmitter
from pishutter.controller import PiShutterController
from pishutter.protocols.shutters import SHUTTERS


STATE_PATH = "/config/pishutter/state.json"

transmitter = CC1101ShutterTransmitter()

controller = PiShutterController(
    transmitter=transmitter,
    state_path=STATE_PATH,
)

# Protect the shared state store and blind movement calculations.
controller_lock = threading.RLock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    transmitter.open()

    try:
        yield
    finally:
        transmitter.close()


app = FastAPI(
    title="PiShutterRemote",
    lifespan=lifespan,
)


class BlindConfiguration(BaseModel):
    open_time_seconds: float | None = None
    close_time_seconds: float | None = None
    safety_buffer_seconds: float | None = None
    position: int | None = None


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
        with controller_lock:
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
        blind = controller.get_blind(blind_key)
        blind.set_position(position)

        return {
            "ok": True,
            "blind": blind_key,
            "position": blind.position,
        }

    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex)) from ex


@app.post("/blinds/{blind_key}/calibrate/closed")
def calibrate_closed(blind_key: str):
    try:
        blind = controller.get_blind(blind_key)
        blind.calibrate_closed()

        return {
            "ok": True,
            "blind": blind_key,
            "position": blind.position,
        }

    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex)) from ex


@app.post("/blinds/{blind_key}/calibrate/open")
def calibrate_open(blind_key: str):
    try:
        blind = controller.get_blind(blind_key)
        blind.calibrate_open()

        return {
            "ok": True,
            "blind": blind_key,
            "position": blind.position,
        }

    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex)) from ex

@app.post("/blinds/{blind_key}/configure")
def configure_blind(
    blind_key: str,
    configuration: BlindConfiguration,
):
    try:
        with controller_lock:
            blind = controller.get_blind(blind_key)

            blind.configure(
                open_time_seconds=configuration.open_time_seconds,
                close_time_seconds=configuration.close_time_seconds,
                safety_buffer_seconds=configuration.safety_buffer_seconds,
                position=configuration.position,
            )

            return {
                "ok": True,
                "blind": blind_key,
                "state": dict(blind.state),
            }

    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex)) from ex

def _send(blind_key: str, command: str):
    try:
        # Do not hold controller_lock for the entire shutter travel time.
        blind = controller.get_blind(blind_key)
        blind.send(command)

        return {
            "ok": True,
            "blind": blind_key,
            "command": command,
        }

    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex)) from ex