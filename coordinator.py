"""Coordinator for SunPower Maxeon integration."""

import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import AsyncConfigEntryAuth
from .const import SYSTEM_DETAILS, POWER_METER, ENERGY_METER, shared_data  # Ensure ENERGY_METER is defined

_LOGGER = logging.getLogger(__name__)

class SunPowerFullCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, shared_data):
        self.api = api
        self.shared_data = shared_data
        super().__init__(hass, _LOGGER, name="Full Coordinator", update_interval=timedelta(minutes=60))

    async def _async_update_data(self):
        systems = await self.api.async_get_systems()
        system = systems.get("systems", [{}])[0]
        system_sn = system.get("system_sn")

        if not system_sn:
            _LOGGER.warning("Missing system_sn in response.")
            raise UpdateFailed("No system serial number")

        self.shared_data["system_sn"] = system_sn
        self.shared_data["system"] = system
        self.shared_data["details"] = await self.api.async_get_system_details(system_sn)
        self.shared_data["power"] = await self.api.async_get_system_power(system_sn)
        self.shared_data["energy"] = await self.api.async_get_system_energy(system_sn)
        self.shared_data["battery_ups"] = await self.api.get_battery_ups_state(system_sn)
        self.shared_data["charging_schedule"] = await self.api.async_get_charging_schedule(system_sn)
        self.shared_data["discharging_schedule"] = await self.api.async_get_discharging_schedule(system_sn)
        self.shared_data["export_limit"] = await self.api.async_get_export_limit(system_sn)

        return dict(self.shared_data)

class SunPowerRealtimeCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, shared_data):
        self.api = api
        self.shared_data = shared_data
        super().__init__(hass, _LOGGER, name="Realtime Coordinator", update_interval=timedelta(seconds=10))

    async def _async_update_data(self):
        system_sn = self.shared_data.get("system_sn")
        if not system_sn:
            raise UpdateFailed("system_sn not initialized yet")

        self.shared_data["power"] = await self.api.async_get_system_power(system_sn)

        return {"power": self.shared_data["power"]}
    
class SunPowerPeriodicCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, shared_data):
        self.api = api
        self.shared_data = shared_data
        super().__init__(hass, _LOGGER, name="Periodic Coordinator", update_interval=timedelta(minutes=10))

    async def _async_update_data(self):
        system_sn = self.shared_data.get("system_sn")
        if not system_sn:
            raise UpdateFailed("system_sn not initialized yet")

        self.shared_data["energy"] = await self.api.async_get_system_energy(system_sn)
        self.shared_data["battery_ups"] = await self.api.get_battery_ups_state(system_sn)
        self.shared_data["charging_schedule"] = await self.api.async_get_charging_schedule(system_sn)
        self.shared_data["discharging_schedule"] = await self.api.async_get_discharging_schedule(system_sn)
        self.shared_data["export_limit"] = await self.api.async_get_export_limit(system_sn)

        return {
            "energy": self.shared_data["energy"],
            "battery_ups": self.shared_data["battery_ups"],
            "charging_schedule": self.shared_data["charging_schedule"],
            "discharging_schedule": self.shared_data["discharging_schedule"],
            "export_limit": self.shared_data["export_limit"],
        }

        