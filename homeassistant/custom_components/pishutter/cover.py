from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiohttp import ClientError

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

API_BASE = "http://local-pishutterremote:8080"
REQUEST_TIMEOUT_SECONDS = 45


async def async_setup_platform(
    hass,
    config,
    async_add_entities,
    discovery_info=None,
) -> None:
    """Set up PiShutterRemote cover entities."""

    session = async_get_clientsession(hass)

    try:
        async with asyncio.timeout(10):
            response = await session.get(f"{API_BASE}/blinds")
            response.raise_for_status()
            blinds = await response.json()
    except (TimeoutError, ClientError) as exc:
        _LOGGER.error("Unable to connect to PiShutterRemote app: %s", exc)
        return

    entities = [
        PiShutterCover(
            key=key,
            name=details["name"],
        )
        for key, details in blinds.items()
    ]

    async_add_entities(entities, update_before_add=True)


class PiShutterCover(CoverEntity):
    """Representation of a PowerSmart shutter."""

    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_should_poll = False
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, key: str, name: str) -> None:
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"pishutter_{key}"

        self._attr_available = True
        self._attr_current_cover_position = 0
        self._attr_is_closed = True

    async def async_update(self) -> None:
        """Retrieve persisted blind state from the app."""

        try:
            data = await self._request("GET", f"/blinds/{self._key}")
            state = data.get("state", {})
            self._set_position(int(state.get("position", 0)))
            self._attr_available = True
        except (TimeoutError, ClientError, ValueError, TypeError) as exc:
            self._attr_available = False
            _LOGGER.warning(
                "Unable to update shutter %s: %s",
                self._key,
                exc,
            )

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open fully and establish a known 100% position."""

        data = await self._request(
            "POST",
            f"/blinds/{self._key}/calibrate/open",
        )
        self._set_position(int(data.get("position", 100)))
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close fully and establish a known 0% position."""

        data = await self._request(
            "POST",
            f"/blinds/{self._key}/calibrate/closed",
        )
        self._set_position(int(data.get("position", 0)))
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop movement."""

        await self._request(
            "POST",
            f"/blinds/{self._key}/stop",
        )

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move to an estimated percentage position."""

        target = max(0, min(100, int(kwargs[ATTR_POSITION])))

        data = await self._request(
            "POST",
            f"/blinds/{self._key}/position/{target}",
        )

        self._set_position(int(data.get("position", target)))
        self.async_write_ha_state()

    async def _request(
        self,
        method: str,
        path: str,
    ) -> dict[str, Any]:
        session = async_get_clientsession(self.hass)

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS):
                response = await session.request(
                    method,
                    f"{API_BASE}{path}",
                )
                response.raise_for_status()
                return await response.json()

        except (TimeoutError, ClientError):
            self._attr_available = False
            self.async_write_ha_state()
            raise

    def _set_position(self, position: int) -> None:
        position = max(0, min(100, position))
        self._attr_current_cover_position = position
        self._attr_is_closed = position == 0
        self._attr_available = True