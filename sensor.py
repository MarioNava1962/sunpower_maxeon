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

from .const import DOMAIN, ENERGY_SENSOR_KEYS
from .coordinator import SunPowerFullCoordinator, SunPowerRealtimeCoordinator, SunPowerPeriodicCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up SunPower Maxeon system sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    periodic_coordinator: SunPowerPeriodicCoordinator = data["periodic"]
    realtime_coordinator: SunPowerRealtimeCoordinator = data["realtime"]
    full_coordinator: SunPowerFullCoordinator = data["full"]

    entities = [
        # Metadata / status
        SunPowerSystemInfo(full_coordinator),

        # Static system detail sensors
        SunPowerDetailSensor(full_coordinator, "battery_capacity",  "kWh"),
        SunPowerDetailSensor(full_coordinator, "installed_pv_power",  "kW"),
        SunPowerDetailSensor(full_coordinator, "inverter_rated_power",  "kW"),
        SunPowerDetailSensor(full_coordinator, "battery_usable_capacity",  "kWh"),
        SunPowerDetailSensor(full_coordinator, "feedin_threshold",  "%"),

        #Power Meter Sensors
        SunPowerPowerSensor(realtime_coordinator, "p_pv",  "W"),
        SunPowerPowerSensor(realtime_coordinator, "p_grid",  "W"),
        SunPowerPowerSensor(realtime_coordinator, "p_storage",  "W"),
        SunPowerPowerSensor(realtime_coordinator, "p_consumption",  "W"),
        SunPowerPowerSensor(realtime_coordinator, "soc",  "%"),

        #Energy Meter Sensors
        SunPowerEnergySensor(periodic_coordinator, "e_pv_generation",  "kWh"),
        SunPowerEnergySensor(periodic_coordinator, "e_storage_charge",  "kWh"),
        SunPowerEnergySensor(periodic_coordinator, "e_storage_discharge", "kWh"),
        SunPowerEnergySensor(periodic_coordinator, "e_grid_import", "kWh"),
        SunPowerEnergySensor(periodic_coordinator, "e_grid_export",  "kWh"),
        SunPowerEnergySensor(periodic_coordinator, "e_consumption",  "kWh"),

        #Schedule Coordinator
        ChargingScheduleSensor(periodic_coordinator),
        DischargingScheduleSensor(periodic_coordinator),

        #Config Sensors        
        BatteryUPSBinarySensor(periodic_coordinator),
        ExportLimitSensor(periodic_coordinator)

    ]

    async_add_entities(entities, True)

class SunPowerEnergySensor(CoordinatorEntity[SunPowerPeriodicCoordinator], SensorEntity):
    """Entity to expose specific SunPower system energy metrics."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SunPowerPeriodicCoordinator,
        key: str,
        unit: Optional[str] = "kWh",
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"s-m_{key}"
        self._attr_should_poll = False
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def translation_key(self) -> str:
        """Return a key for translation/localization."""
        return self._key

    @property
    def native_value(self) -> Optional[float | int | str]:
        """Return the sensor's current value."""
        return self.coordinator.data.get("energy", {}).get(self._key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def device_info(self) -> dict:
        """Return device info for the system."""
        system_sn = self.coordinator.shared_data.get("system_sn", "unknown")
        return {
            "identifiers": {(DOMAIN, system_sn)},
            "manufacturer": "SunPower",
            "model": self.coordinator.shared_data.get("inverter_model", "Unknown"),
            "sw_version": self.coordinator.shared_data.get("inv_version"),
        }

    @property
    def icon(self) -> str:
        """Return an MDI icon based on the key."""
        icon_map = {
            "e_pv_generation": "mdi:solar-panel",
            "e_storage_charge": "mdi:battery-arrow-up",
            "e_storage_discharge": "mdi:battery-arrow-down",
            "e_grid_import": "mdi:transmission-tower-import",
            "e_grid_export": "mdi:transmission-tower-export",
            "e_consumption": "mdi:home-lightning-bolt",
        }
        return icon_map.get(self._key, "mdi:gauge")
    
class SunPowerPowerSensor(CoordinatorEntity[SunPowerRealtimeCoordinator], SensorEntity):
    """Sensor entity for real-time SunPower power readings and battery SoC."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SunPowerRealtimeCoordinator,
        key: str,
        unit: Optional[str] = "W",
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"s-m_{key}"
        self._attr_should_poll = False

        if key == "soc":
            self._attr_device_class = SensorDeviceClass.BATTERY
            self._attr_native_unit_of_measurement = "%"
            self._attr_icon = "mdi:battery"
        else:
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_native_unit_of_measurement = "W"

        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def translation_key(self) -> str:
        """Return a key for translation/localization."""
        return self._key

    @property
    def native_value(self) -> Optional[float | int | str]:
        """Return the sensor's current value."""
        return self.coordinator.shared_data.get("energy", {}).get(self._key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def device_info(self) -> dict:
        """Return device info for the system."""
        system_sn = self.coordinator.shared_data.get("system_sn", "unknown")
        return {
            "identifiers": {(DOMAIN, system_sn)},
            "manufacturer": "SunPower",
            "model": self.coordinator.shared_data.get("inverter_model", "Unknown"),
            "sw_version": self.coordinator.shared_data.get("inv_version"),
        }

    @property
    def icon(self) -> str:
        """Return an MDI icon based on the key."""
        if self._key == "soc":
            soc = self.native_value
            if soc is None:
                return "mdi:battery-unknown"
            soc = max(0, min(100, int(soc)))
            return f"mdi:battery-{soc // 10 * 10}" if soc < 100 else "mdi:battery"
        icon_map = {
            "p_pv": "mdi:solar-panel",
            "p_consumption": "mdi:home-lightning-bolt",
            "p_grid": "mdi:transmission-tower-export",
            "p_storage": "mdi:battery",
        }
        return icon_map.get(self._key, "mdi:gauge")
    
class SunPowerDetailSensor(CoordinatorEntity[SunPowerFullCoordinator], SensorEntity):
    """Entity to expose static SunPower system details."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: SunPowerFullCoordinator,
        key: str,
        unit: Optional[str] = None,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"sunpower_{key}"
        self._attr_native_unit_of_measurement = unit

        # Assign device class if applicable
        if key in ["battery_capacity", "battery_usable_capacity"]:
            self._attr_device_class = SensorDeviceClass.ENERGY
        elif key in ["installed_pv_power", "inverter_rated_power"]:
            self._attr_device_class = SensorDeviceClass.POWER

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
        """Return device info for the system."""
        system_sn = self.coordinator.shared_data.get("system_sn", "unknown")
        return {
            "identifiers": {(DOMAIN, system_sn)},
            "manufacturer": "SunPower",
            "model": self.coordinator.shared_data.get("inverter_model", "Unknown"),
            "sw_version": self.coordinator.shared_data.get("inv_version"),
        }

    @property
    def icon(self) -> str:
        """Return an appropriate icon for the sensor."""
        if "battery" in self._key:
            return "mdi:battery"
        if "pv_power" in self._key or "inverter" in self._key:
            return "mdi:solar-power"
        return "mdi:gauge"

class SunPowerSystemInfo(CoordinatorEntity[SunPowerFullCoordinator], SensorEntity):
    """Entity to expose SunPower system status and metadata."""

    def __init__(self, coordinator: SunPowerFullCoordinator) -> None:
        super().__init__(coordinator)
        
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
        return self.coordinator.shared_data
    
    @property
    def translation_key(self) -> str:
        """Return the translation key to localize the entity name."""
        return "sunpower_maxeon_system"

   
class ChargingScheduleSensor(CoordinatorEntity[SunPowerPeriodicCoordinator], SensorEntity):
    """Sensor for the SunPower charging schedule."""

    _attr_has_entity_name = True
    
    _attr_unique_id = "sunpower_charging_schedule"
    _attr_icon = "mdi:calendar-clock"  # Shows a calendar with clock icon

    def __init__(self, coordinator: SunPowerPeriodicCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

    @property
    def state(self) -> str:
        schedule = self.schedule
        return "enabled" if schedule.get("enable") else "disabled"
    
    @property
    def device_info(self) -> dict:
        """Return device info for the system."""
        system_sn = self.coordinator.shared_data.get("system_sn", "unknown")
        return {
            "identifiers": {(DOMAIN, system_sn)},
            "manufacturer": "SunPower",
            "model": self.coordinator.shared_data.get("inverter_model", "Unknown"),
            "sw_version": self.coordinator.shared_data.get("inv_version"),
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
    
class DischargingScheduleSensor(CoordinatorEntity[SunPowerPeriodicCoordinator], SensorEntity):
    """Sensor for the SunPower discharging schedule."""

    _attr_has_entity_name = True
    
    _attr_unique_id = "sunpower_discharging_schedule"
    _attr_icon = "mdi:calendar-clock"  # Shows a calendar with clock icon

    def __init__(self, coordinator: SunPowerPeriodicCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

    @property
    def state(self) -> str:
        schedule = self.schedule
        return "enabled" if schedule.get("enable") else "disabled"
    
    @property
    def device_info(self) -> dict:
        """Return device info for the system."""
        system_sn = self.coordinator.shared_data.get("system_sn", "unknown")
        return {
            "identifiers": {(DOMAIN, system_sn)},
            "manufacturer": "SunPower",
            "name": f"SunPower System {system_sn}",
            "model": self.coordinator.shared_data.get("inverter_model", "Unknown"),
            "sw_version": self.coordinator.shared_data.get("inv_version"),
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

class BatteryUPSBinarySensor(CoordinatorEntity[SunPowerPeriodicCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    
    def __init__(self, coordinator: SunPowerPeriodicCoordinator):
        super().__init__(coordinator)
        
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
        """Return device info for the system."""
        system_sn = self.coordinator.shared_data.get("system_sn", "unknown")
        return {
            "identifiers": {(DOMAIN, system_sn)},
            "manufacturer": "SunPower",
            "name": f"SunPower System {system_sn}",
            "model": self.coordinator.shared_data.get("inverter_model", "Unknown"),
            "sw_version": self.coordinator.shared_data.get("inv_version"),
        }
    
    @property
    def translation_key(self) -> str:
        """Return the translation key to localize the entity name."""
        return "ups_enabled"

class ExportLimitSensor(CoordinatorEntity[SunPowerPeriodicCoordinator], SensorEntity):
    """Sensor for the export limit setting."""

    _attr_has_entity_name = True
    
    _attr_unique_id = "sunpower_export_limit"
    _attr_icon = "mdi:transmission-tower-export"

    def __init__(self, coordinator: SunPowerPeriodicCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def state(self) -> str:
        return "enabled" if self.coordinator.data.get("export_limit", {}).get("enable") else "disabled"

    @property
    def extra_state_attributes(self) -> dict:
        return self.coordinator.data.get("export_limit", {})

    @property
    def device_info(self) -> dict:
        """Return device info for the system."""
        system_sn = self.coordinator.shared_data.get("system_sn", "unknown")
        return {
            "identifiers": {(DOMAIN, system_sn)},
            "manufacturer": "SunPower",
            "name": f"SunPower System {system_sn}",
            "model": self.coordinator.shared_data.get("inverter_model", "Unknown"),
            "sw_version": self.coordinator.shared_data.get("inv_version"),
        }

    @property
    def translation_key(self) -> str:
        """Return the translation key to localize the entity name."""
        return "feedin_threshold"