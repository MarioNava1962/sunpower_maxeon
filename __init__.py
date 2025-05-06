from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow

from .const import DOMAIN
from . import api
from .coordinator import SunPowerCoordinator
from .config_flow import OptionsFlowHandler  # 👈 Add this

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

type SunPowerConfigEntry = ConfigEntry[SunPowerCoordinator]

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Options updated; reloading config entry.")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SunPower Maxeon from a config entry."""
    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, entry)
    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

    auth = api.AsyncConfigEntryAuth(
        aiohttp_client.async_get_clientsession(hass), session
    )

    coordinator = SunPowerCoordinator(hass, auth)

    try:
        await coordinator.async_config_entry_first_refresh()
        if not coordinator.data:
            raise ConfigEntryNotReady("No systems found in SunPower account.")
    except Exception as err:
        raise ConfigEntryNotReady(f"Error connecting to SunPower API: {err}") from err

    # Get system_sn and fetch charging schedule
    system_sn = coordinator.data.get("system_sn")
    if system_sn:
        try:
            charging_schedule = await auth.async_get_charging_schedule(system_sn)
            discharging_schedule = await auth.async_get_discharging_schedule
            coordinator.data["charging_schedule"] = charging_schedule
        except Exception as err:
            _LOGGER.warning("Failed to fetch charging schedule for system %s: %s", system_sn, err)
    else:
        _LOGGER.warning("No system_sn found in coordinator data. Skipping charging schedule fetch.")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SunPowerConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok