import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    system_sn = coordinator.data["system_sn"]

    async_add_entities([
        BatteryUPSSwitch(coordinator, system_sn)
    ])

class BatteryUPSSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, system_sn):
        super().__init__(coordinator)
        self._attr_name = "Backup UPS"
        self._attr_unique_id = f"{system_sn}_battery_ups"
        self.system_sn = system_sn
        self._state = None

    @property
    def is_on(self) -> bool:
        """Return whether the UPS is enabled based on the 'enable' value in the coordinator data."""
        return self.coordinator.data.get("battery_ups", {}).get("enable", False)

    async def async_turn_on(self, **kwargs):
        """Turn the UPS on."""
        await self._set_battery_ups_state(True)

    async def async_turn_off(self, **kwargs):
        """Turn the UPS off."""
        await self._set_battery_ups_state(False)

    async def _set_battery_ups_state(self, enable: bool):
        """Set the battery UPS state and handle the change."""
        try:
            await self.coordinator.api.set_battery_ups_state(self.system_sn, enable)
            # Optimistic update: directly change the state for immediate feedback
            self._state = enable  
            self.async_write_ha_state()  # Reflect change immediately in HA
        except Exception as e:
            _LOGGER.error("Failed to set battery UPS state: %s", e)
        finally:
            # Refresh the coordinator data to sync state
            await self.coordinator.async_request_refresh()

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
        """Return the icon based on whether the UPS is enabled or not."""
        if self.is_on:
            return "mdi:battery"  # Icon when UPS is enabled
        else:
            return "mdi:battery-off"  # Icon when UPS is disabled
