"""Coordinator for SunPower Maxeon integration."""

import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .api import AsyncConfigEntryAuth
from .const import SYSTEM_DETAILS

_LOGGER = logging.getLogger(__name__)


class SunPowerCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching data from the SunPower Maxeon API."""

    def __init__(self, hass, api: AsyncConfigEntryAuth):
        """Initialize the coordinator."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name="SunPower Maxeon",
            update_interval=timedelta(minutes=1),
        )

    async def _async_update_data(self):
        """Fetch and merge system and detail data from the API, fallback on failure."""
        try:
            systems_data = await self.api.async_get_systems()

            if not systems_data.get("systems"):
                _LOGGER.warning("No systems returned, using dummy system details")
                return SYSTEM_DETAILS["default"]

            system = systems_data["systems"][0]
            system_sn = system.get("system_sn")

            if not system_sn:
                _LOGGER.warning("Missing system_sn in response, using dummy system details")
                return SYSTEM_DETAILS["default"]
            
            details_data = await self.api.async_get_system_details(system_sn)

            # Merge both dictionaries
            merged = {**system, **details_data}
            return merged

        except Exception as err:
            _LOGGER.error("Failed to fetch system data: %s", err)
            return SYSTEM_DETAILS["default"]
