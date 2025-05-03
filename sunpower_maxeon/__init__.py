"""The SunPower Maxeon integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow
from .const import DOMAIN
from . import api

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
_PLATFORMS: list[Platform] = [Platform.SENSOR]

# TODO Create ConfigEntry type alias with ConfigEntryAuth or AsyncConfigEntryAuth object
# TODO Rename type alias and update all entry annotations
type SunPowerConfigEntry = ConfigEntry[api.AsyncConfigEntryAuth]

# # TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SunPower Maxeon from a config entry."""
    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, entry)
    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

    auth = api.AsyncConfigEntryAuth(
        aiohttp_client.async_get_clientsession(hass), session
    )

    try:
        # Test API connection by fetching systems
        systems = await auth.async_get_systems()
        if not systems.get("systems"):
            raise ConfigEntryNotReady("No systems found in SunPower account.")
    except Exception as err:
        raise ConfigEntryNotReady(f"Error connecting to SunPower API: {err}") from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = auth

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True
    """Set up SunPower Maxeon from a config entry."""
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    )

    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

    # Create the API client
    auth = api.AsyncConfigEntryAuth(
        aiohttp_client.async_get_clientsession(hass), session
    )

    # Store in hass.data so platforms can access it
    hass.data.setdefault("sunpower_maxeon", {})[entry.entry_id] = auth

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True



# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: SunPowerConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    if unload_ok:
        hass.data["sunpower_maxeon"].pop(entry.entry_id, None)
    return unload_ok
