"""Sensor platform for SunPower Maxeon integration."""

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SunPowerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up SunPower Maxeon system info sensor."""
    coordinator: SunPowerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SunPowerSystemInfo(coordinator)], True)


class SunPowerSystemInfo(CoordinatorEntity, Entity):
    """Entity to expose SunPower system status and metadata."""

    def __init__(self, coordinator: SunPowerCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "SunPower Maxeon System"
        self._attr_unique_id = "sunpower_device_info"
        self._attr_should_poll = False

    @property
    def state(self):
        """Return the system status as the main state."""
        return self.coordinator.data.get("status", "unknown")

    @property
    def available(self):
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def device_info(self):
        """Return device metadata for the system."""
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
