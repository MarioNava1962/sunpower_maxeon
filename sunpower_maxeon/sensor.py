"""Sensor platform for SunPower Maxeon integration."""

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .api import AsyncConfigEntryAuth

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up SunPower Maxeon system info entity."""
    auth: AsyncConfigEntryAuth = hass.data[DOMAIN][entry.entry_id]

    async def async_update_data():
        """Fetch system details."""
        try:
            systems = await auth.async_get_systems()
            if not systems.get("systems"):
                raise UpdateFailed("No systems found.")
            system_info = systems["systems"][0]
            return system_info
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sunpower_maxeon_device_info",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([SunPowerSystemInfo(coordinator)], True)


class SunPowerSystemInfo(Entity):
    """Entity to expose SunPower system status and metadata."""

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "SunPower Maxeon System"
        self._attr_unique_id = "sunpower_device_info"
        self._attr_should_poll = False

    async def async_update(self):
        await self.coordinator.async_request_refresh()

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def should_poll(self):
        return False

    @property
    def state(self):
        """Return the system status as the main state."""
        return self.coordinator.data.get("status", "unknown")

    @property
    def device_info(self):
        data = self.coordinator.data
        return {
            "identifiers": {(DOMAIN, data.get("system_sn", "unknown"))},
            "name": "SunPower Maxeon System",
            "manufacturer": "SunPower",
            "model": data.get("inverter_model", "Unknown"),
            "sw_version": data.get("inv_version"),
        }

    @property
    def extra_state_attributes(self):
        """Expose all API fields as attributes."""
        return self.coordinator.data
