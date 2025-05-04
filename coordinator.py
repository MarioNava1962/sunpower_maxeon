"""Coordinator for SunPower Maxeon integration."""

import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .api import AsyncConfigEntryAuth
from .const import SYSTEM_DETAILS, POWER_METER  # assuming POWER_METER is your fallback

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
        """Fetch and merge system, detail, and power data from the API."""
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
            power_data = await self.api.async_get_system_power(system_sn)

            # Merge system metadata, details, and power data
            merged = {**system, **details_data, **power_data}
            return merged

        except Exception as err:
            _LOGGER.error("Failed to fetch system data: %s", err)
            return {**SYSTEM_DETAILS["default"], **POWER_METER}
