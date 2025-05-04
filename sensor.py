"""Sensor platform for SunPower Maxeon integration."""

import logging
from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)

from .const import DOMAIN
from .coordinator import SunPowerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up SunPower Maxeon system sensors."""
    coordinator: SunPowerCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        # Metadata / status
        SunPowerSystemInfo(coordinator),

        # Static system detail sensors
        SunPowerDetailSensor(coordinator, "battery_capacity", "Battery Capacity", "kWh"),
        SunPowerDetailSensor(coordinator, "installed_pv_power", "Installed PV Power", "kW"),
        SunPowerDetailSensor(coordinator, "inverter_rated_power", "Inverter Rated Power", "kW"),
        SunPowerDetailSensor(coordinator, "battery_usable_capacity", "Battery Usable Capacity", "kWh"),
        SunPowerDetailSensor(coordinator, "feedin_threshold", "Feed-In Threshold", "%"),

        # Real-time power sensors
        SunPowerDetailSensor(coordinator, "production_kw", "PV Production", "kW"),
        SunPowerDetailSensor(coordinator, "consumption_kw", "Home Consumption", "kW"),
        SunPowerDetailSensor(coordinator, "feedin_kw", "Grid Feed-In", "kW"),
        SunPowerDetailSensor(coordinator, "self_consumption_kw", "Self Consumption", "kW"),
    ]

    async_add_entities(entities, True)



class SunPowerSystemInfo(CoordinatorEntity, SensorEntity):
    """Entity to expose SunPower system status and metadata."""

    def __init__(self, coordinator: SunPowerCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "SunPower Maxeon System"
        self._attr_unique_id = "sunpower_device_info"
        self._attr_should_poll = False
        self._attr_icon = "mdi:solar-power"

    @property
    def native_value(self) -> str:
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


class SunPowerDetailSensor(CoordinatorEntity, SensorEntity):
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

        # Assign device class and state class if applicable
        if key in ["battery_capacity", "battery_usable_capacity"]:
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.TOTAL
        elif key in ["installed_pv_power", "inverter_rated_power"]:
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif key == "feedin_threshold":
            self._attr_device_class = SensorDeviceClass.POWER_FACTOR
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif key in ["production_kw", "consumption_kw", "feedin_kw", "self_consumption_kw"]:
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[float | int | str]:
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

    @property
    def icon(self) -> str:
        """Return a suitable MDI icon for the sensor."""
        if "battery" in self._key:
            return "mdi:battery"
        elif "pv_power" in self._key or "inverter" in self._key:
            return "mdi:solar-power"
        elif "threshold" in self._key:
            return "mdi:percent"
        elif self._key == "production_kw":
            return "mdi:solar-panel"
        elif self._key == "consumption_kw":
            return "mdi:transmission-tower"
        elif self._key == "feedin_kw":
            return "mdi:transmission-tower-export"
        elif self._key == "self_consumption_kw":
            return "mdi:home-lightning-bolt"
        return "mdi:gauge"
