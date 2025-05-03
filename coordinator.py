"""Coordinator for SunPower Maxeon integration."""

import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AsyncConfigEntryAuth

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
        """Fetch and merge system and detail data from the API."""
        try:
            systems_data = await self.api.async_get_systems()
            system = systems_data["systems"][0]  # or handle multiple systems dynamically
            details_data = await self.api.async_get_system_details(system["system_sn"])

            # Merge both dictionaries
            merged = {**system, **details_data}
            return merged

        except Exception as err:
            raise UpdateFailed(f"Failed to fetch data: {err}") from err

