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
        self._attr_name = "Battery UPS Enabled"
        self._attr_unique_id = f"{system_sn}_battery_ups"
        self.system_sn = system_sn
        self._state = None

    @property
    def is_on(self) -> bool:
        # Use local state override if recently changed
        return self._state if self._state is not None else self.coordinator.data.get("battery_ups", {}).get("enable", False)

    async def async_turn_on(self, **kwargs):
        await self._set_battery_ups_state(True)

    async def async_turn_off(self, **kwargs):
        await self._set_battery_ups_state(False)

    async def _set_battery_ups_state(self, enable: bool):
        try:
            await self.coordinator.api.set_battery_ups_state(self.system_sn, enable)
            self._state = enable  # Optimistic update
            self.async_write_ha_state()  # Reflect change immediately in HA
        except Exception as e:
            _LOGGER.error("Failed to set battery UPS state: %s", e)
        finally:
            await self.coordinator.async_request_refresh()
            self._state = None  # Reset override after refresh

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