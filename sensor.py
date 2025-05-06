"""Sensor platform for SunPower Maxeon integration."""

import logging
from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.binary_sensor import BinarySensorEntity
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
        SunPowerDetailSensor(coordinator, "battery_capacity",  "kWh"),
        SunPowerDetailSensor(coordinator, "installed_pv_power",  "kW"),
        SunPowerDetailSensor(coordinator, "inverter_rated_power",  "kW"),
        SunPowerDetailSensor(coordinator, "battery_usable_capacity",  "kWh"),
        SunPowerDetailSensor(coordinator, "feedin_threshold",  "%"),

        #Power Meter Sensors
        SunPowerDetailSensor(coordinator, "p_pv",  "W"),
        SunPowerDetailSensor(coordinator, "p_grid",  "W"),
        SunPowerDetailSensor(coordinator, "p_storage",  "W"),
        SunPowerDetailSensor(coordinator, "p_consumption",  "W"),
        SunPowerDetailSensor(coordinator, "soc",  "%"),

        #Energy Meter Sensors
        SunPowerDetailSensor(coordinator, "e_pv_generation",  "Wh"),
        SunPowerDetailSensor(coordinator, "e_storage_charge",  "Wh"),
        SunPowerDetailSensor(coordinator, "e_storage_discharge", "Wh"),
        SunPowerDetailSensor(coordinator, "e_grid_import", "Wh"),
        SunPowerDetailSensor(coordinator, "e_grid_export",  "Wh"),
        SunPowerDetailSensor(coordinator, "e_consumption",  "Wh"),

        #Schedule Coordinator
        ChargingScheduleSensor(coordinator),
        DischargingScheduleSensor(coordinator),

        #Config Sensors        
        BatteryUPSBinarySensor(coordinator),
        ExportLimitSensor(coordinator)

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

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SunPowerCoordinator,
        key: str,
        unit: Optional[str] = None,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"sm_{key}"
        self._attr_should_poll = True
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
        elif key in [
            "production_kw", "consumption_kw", "feedin_kw", "self_consumption_kw",
            "p_pv", "p_consumption", "p_grid", "p_storage"
        ]:
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif key == "soc":
            self._attr_device_class = SensorDeviceClass.BATTERY
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = "%"
        elif key in [
            "e_pv_generation", "e_storage_charge", "e_storage_discharge",
            "e_grid_import", "e_grid_export", "e_consumption"
        ]:
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def translation_key(self) -> str:
        """Return the translation key to localize the entity name."""
        return self._key

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
            "manufacturer": "SunPower",
            "model": data.get("inverter_model", "Unknown"),
            "sw_version": data.get("inv_version"),
        }

    @property
    def icon(self) -> str:
        """Return a suitable MDI icon for the sensor."""
        if self._key == "soc":
            if self.native_value is None:
                return "mdi:battery-unknown"
            soc = max(0, min(100, int(self.native_value)))
            icon_level = (soc // 10) * 10
            return f"mdi:battery-{icon_level}" if soc < 100 else "mdi:battery"
        if "battery" in self._key:
            return "mdi:battery"
        if "pv_power" in self._key or "inverter" in self._key:
            return "mdi:solar-power"
        if "threshold" in self._key:
            return "mdi:percent"
        if self._key in ("production_kw", "p_pv"):
            return "mdi:solar-panel"
        if self._key in ("consumption_kw", "p_consumption"):
            return "mdi:transmission-tower"
        if self._key in ("feedin_kw", "p_grid"):
            return "mdi:transmission-tower-export"
        if self._key == "self_consumption_kw":
            return "mdi:home-lightning-bolt"
        if self._key == "p_storage":
            return "mdi:battery"
        if self._key == "e_grid_import":
            return "mdi:transmission-tower-import"
        if self._key == "e_grid_export":
            return "mdi:transmission-tower-export"
        if self._key == "e_consumption":
            return "mdi:home-lightning-bolt"
        if self._key == "e_pv_generation":
            return "mdi:solar-panel"
        if self._key == "e_storage_charge":
            return "mdi:battery-arrow-up"
        if self._key == "e_storage_discharge":
            return "mdi:battery-arrow-down"
        if self._key.startswith("e_"):
            return "mdi:lightning-bolt-circle"
        return "mdi:gauge"

    
class ChargingScheduleSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the SunPower charging schedule."""

    _attr_has_entity_name = True
    
    _attr_unique_id = "sunpower_charging_schedule"
    _attr_icon = "mdi:calendar-clock"  # Shows a calendar with clock icon

    def __init__(self, coordinator: SunPowerCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

    @property
    def state(self) -> str:
        schedule = self.schedule
        return "enabled" if schedule.get("enable") else "disabled"
    
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
        schedule = self.schedule
        return {
            "start_time_1": schedule.get("start_time_1"),
            "end_time_1": schedule.get("end_time_1"),
            "start_time_2": schedule.get("start_time_2"),
            "end_time_2": schedule.get("end_time_2"),
            "max_soc": schedule.get("max_soc"),
        }

    @property
    def schedule(self) -> dict:
        return self.coordinator.data.get("charging_schedule", {})
    
    @property
    def translation_key(self) -> str:
        """Return the translation key to localize the entity name."""
        return "charging_schedule"
    
class DischargingScheduleSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the SunPower discharging schedule."""

    _attr_has_entity_name = True
    
    _attr_unique_id = "sunpower_discharging_schedule"
    _attr_icon = "mdi:calendar-clock"  # Shows a calendar with clock icon

    def __init__(self, coordinator: SunPowerCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

    @property
    def state(self) -> str:
        schedule = self.schedule
        return "enabled" if schedule.get("enable") else "disabled"
    
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
        schedule = self.schedule
        return {
            "start_time_1": schedule.get("start_time_1"),
            "end_time_1": schedule.get("end_time_1"),
            "start_time_2": schedule.get("start_time_2"),
            "end_time_2": schedule.get("end_time_2"),
            "min_soc": schedule.get("min_soc"),
        }

    @property
    def schedule(self) -> dict:
        return self.coordinator.data.get("discharging_schedule", {})
    
    @property
    def translation_key(self) -> str:
        """Return the translation key to localize the entity name."""
        return "discharging_schedule"

class BatteryUPSBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Battery UPS Enabled"
        self._attr_unique_id = "sunpower_ups"
        self._attr_device_class = SensorDeviceClass.POWER

    @property
    def is_on(self) -> bool:
        """Return True if UPS is enabled."""
        return self.coordinator.data.get("battery_ups", {}).get("enable", False)

    @property
    def icon(self) -> str:
        """Return an icon based on UPS state."""
        return "mdi:battery" if self.is_on else "mdi:battery-off"

    @property
    def device_info(self) -> dict:
        """Return device metadata for this sensor."""
        data = self.coordinator.data
        return {
            "identifiers": {(DOMAIN, data.get("system_sn", "unknown"))},
            "name": "SunPower Maxeon System",
            "manufacturer": "SunPower",
            "model": data.get("inverter_model", "Unknown"),
            "sw_version": data.get("inv_version"),
        }

class ExportLimitSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the export limit setting."""

    _attr_has_entity_name = True
    _attr_name = "Export Limit"
    _attr_unique_id = "sunpower_export_limit"
    _attr_icon = "mdi:transmission-tower-export"

    def __init__(self, coordinator: SunPowerCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def state(self) -> str:
        return "enabled" if self.coordinator.data.get("export_limit", {}).get("enable") else "disabled"

    @property
    def extra_state_attributes(self) -> dict:
        return self.coordinator.data.get("export_limit", {})

    @property
    def device_info(self) -> dict:
        data = self.coordinator.data
        return {
            "identifiers": {(DOMAIN, data.get("system_sn", "unknown"))},
            "name": "SunPower Maxeon System",
            "manufacturer": "SunPower",
            "model": data.get("inverter_model", "Unknown"),
            "sw_version": data.get("inv_version"),
        }
