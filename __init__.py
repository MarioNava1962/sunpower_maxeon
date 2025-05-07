from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow

from .const import DOMAIN, shared_data
from . import api
from .coordinator import SunPowerFullCoordinator, SunPowerRealtimeCoordinator, SunPowerPeriodicCoordinator
from .config_flow import OptionsFlowHandler

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [Platform.SENSOR]

type SunPowerConfigEntry = ConfigEntry[SunPowerFullCoordinator]

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

    # Create all coordinators
    full_coordinator = SunPowerFullCoordinator(hass, auth, shared_data)
    realtime_coordinator = SunPowerRealtimeCoordinator(hass, auth, shared_data)
    periodic_coordinator = SunPowerPeriodicCoordinator(hass, auth, shared_data)

    try:
        await full_coordinator.async_config_entry_first_refresh()
        await realtime_coordinator.async_config_entry_first_refresh()
        await periodic_coordinator.async_config_entry_first_refresh()

        if not shared_data.get("system_sn"):
            raise ConfigEntryNotReady("No systems found in SunPower account.")

    except Exception as err:
        raise ConfigEntryNotReady(f"Error connecting to SunPower API: {err}") from err

    # Store coordinators in hass.data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "full": full_coordinator,
        "realtime": realtime_coordinator,
        "periodic": periodic_coordinator,
        "shared_data": shared_data,
    }

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True



async def async_unload_entry(hass: HomeAssistant, entry: SunPowerConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok