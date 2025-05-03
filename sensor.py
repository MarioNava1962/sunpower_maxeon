"""Sensor platform for SunPower Maxeon integration."""

import logging
from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SunPowerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up SunPower Maxeon system sensors."""
    coordinator: SunPowerCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        SunPowerSystemInfo(coordinator),
        SunPowerDetailSensor(coordinator, "battery_capacity", "Battery Capacity", "kWh"),
        SunPowerDetailSensor(coordinator, "installed_pv_power", "Installed PV Power", "kW"),
        SunPowerDetailSensor(coordinator, "inverter_rated_power", "Inverter Rated Power", "kW"),
        SunPowerDetailSensor(coordinator, "battery_usable_capacity", "Battery Usable Capacity", "kWh"),
        SunPowerDetailSensor(coordinator, "feedin_threshold", "Feed-In Threshold", "%"),
    ]

    async_add_entities(entities, True)


class SunPowerSystemInfo(CoordinatorEntity, Entity):
    """Entity to expose SunPower system status and metadata."""

    def __init__(self, coordinator: SunPowerCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "SunPower Maxeon System"
        self._attr_unique_id = "sunpower_device_info"
        self._attr_should_poll = False

    @property
    def state(self) -> str:
        """Return the system status as the main state."""
        return self.coordinator.data.get("status", "unknown")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def device_info(self) -> dict:
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
    def extra_state_attributes(self) -> dict:
        """Expose all API fields as attributes."""
        return self.coordinator.data


class SunPowerDetailSensor(CoordinatorEntity, Entity):
    """Entity to expose specific SunPower system detail fields."""

    def __init__(
        self,
        coordinator: SunPowerCoordinator,
        key: str,
        name: str,
        unit: Optional[str] = None,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"sunpower_{key}"
        self._attr_should_poll = False
        self._attr_native_unit_of_measurement = unit

    @property
    def state(self) -> Optional[float | int | str]:
        """Return the value for the specific system detail field."""
        return self.coordinator.data.get(self._key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def device_info(self) -> dict:
        """Inherit device metadata from the main system entity."""
        data = self.coordinator.data
        return {
            "identifiers": {(DOMAIN, data.get("system_sn", "unknown"))},
            "name": "SunPower Maxeon System",
            "manufacturer": "SunPower",
            "model": data.get("inverter_model", "Unknown"),
            "sw_version": data.get("inv_version"),
        }

