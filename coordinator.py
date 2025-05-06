"""Coordinator for SunPower Maxeon integration."""

import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .api import AsyncConfigEntryAuth
from .const import SYSTEM_DETAILS, POWER_METER, ENERGY_METER  # Ensure ENERGY_METER is defined

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
        """Fetch and merge system, detail, power, energy, battery, and charging schedule data from the API."""
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

            # Fetch all data
            details_data = await self.api.async_get_system_details(system_sn)
            power_data = await self.api.async_get_system_power(system_sn)
            energy_data = await self.api.async_get_system_energy(system_sn)
            battery_ups_data = await self.api.get_battery_ups_state(system_sn)
            charging_schedule = await self.api.async_get_charging_schedule(system_sn)
            discharging_schedule = await self.api.async_get_discharging_schedule(system_sn)

            merged = {
                **system,
                **details_data,
                **power_data,
                **energy_data,
                "battery_ups": battery_ups_data,
                "charging_schedule": charging_schedule,
                "discharging_schedule": discharging_schedule,
                "system_sn": system_sn,
            }

            return merged

        except Exception as err:
            _LOGGER.error("Failed to fetch system data: %s", err)
            return {
                **SYSTEM_DETAILS["default"],
                **POWER_METER,
                **ENERGY_METER,
                "battery_ups": {"enable": False},
                "charging_schedule": {},  # Fallback default
                "system_sn": "unknown",
            }
