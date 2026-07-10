import sys
sys.path.insert(0, "/config/PiShutterRemote/src")

import asyncio
from functools import partial

from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
    ATTR_POSITION,
)
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import EntityCategory

import inspect
import pishutter.controller as pishutter_controller

from pishutter.controller import PiShutterController

raise RuntimeError(
    f"PiShutterController loaded from: {inspect.getfile(PiShutterController)} "
    f"with signature: {inspect.signature(PiShutterController.__init__)}"
)
from pishutter.protocols.shutters import SHUTTERS

STATE_PATH = "/config/pishutter/state.json"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = [
        PiShutterCover(key, remote.name)
        for key, remote in SHUTTERS.items()
    ]
    async_add_entities(entities)


class PiShutterCover(CoverEntity):
    def __init__(self, key: str, name: str):
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"pishutter_{key}"
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )
        self._attr_current_cover_position = 0
        self._attr_is_closed = True

    async def async_added_to_hass(self):
        await self._load_state()

    async def _load_state(self):
        def load():
            with PiShutterController(state_path=STATE_PATH) as controller:
                blind = controller.get_blind(self._key)
                return blind.position

        position = await self.hass.async_add_executor_job(load)
        self._attr_current_cover_position = position
        self._attr_is_closed = position == 0

    async def async_open_cover(self, **kwargs):
        await self._run_command("calibrate_open")

    async def async_close_cover(self, **kwargs):
        await self._run_command("calibrate_closed")

    async def async_stop_cover(self, **kwargs):
        await self._run_command("stop")

    async def async_set_cover_position(self, **kwargs):
        position = kwargs[ATTR_POSITION]
        await self._run_command("position", position)

    async def _run_command(self, action: str, value=None):
        def run():
            with PiShutterController(state_path=STATE_PATH) as controller:
                blind = controller.get_blind(self._key)

                if action == "calibrate_open":
                    blind.calibrate_open()
                elif action == "calibrate_closed":
                    blind.calibrate_closed()
                elif action == "stop":
                    blind.stop()
                elif action == "position":
                    blind.set_position(value)

                return blind.position

        position = await self.hass.async_add_executor_job(run)

        self._attr_current_cover_position = position
        self._attr_is_closed = position == 0
        self.async_write_ha_state()
