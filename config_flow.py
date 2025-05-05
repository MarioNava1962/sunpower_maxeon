"""Config flow for SunPower Maxeon."""
from collections.abc import Mapping
from typing import Any
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    TimeSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import DOMAIN
from .api import AsyncConfigEntryAuth

_LOGGER = logging.getLogger(__name__)

class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle SunPower Maxeon OAuth2 authentication."""

    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @property
    def extra_authorize_data(self) -> dict[str, str]:
        """Extra data that needs to be appended to the authorize url."""
        return {"scope": "offline_access system.read"}

    async def async_oauth_create_entry(self, data: dict) -> FlowResult:
        """Create an oauth config entry or update existing entry for reauth."""
        existing_entry = await self.async_set_unique_id(DOMAIN)
        if existing_entry:
            self.hass.config_entries.async_update_entry(existing_entry, data=data)
            await self.hass.config_entries.async_reload(existing_entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        return await super().async_oauth_create_entry(data)

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle a flow start."""
        await self.async_set_unique_id(DOMAIN)

        if self.source != config_entries.SOURCE_REAUTH and self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return await super().async_step_user(user_input)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for SunPower Maxeon."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Initial step: let user choose which section to configure."""
        if user_input is not None:
            section = user_input["section"]
            if section == "charging":
                return await self.async_step_charging()
            elif section == "discharging":
                return await self.async_step_discharging()
            elif section == "export":
                return await self.async_step_export()

        return self.async_show_form(
            step_id="init",
            data_schema=config_entries.vol.Schema({
                config_entries.vol.Required("section"): config_entries.vol.In({
                    "charging": "⚡ Charging Schedule",
                    "discharging": "🔋 Discharging Schedule",
                    "export": "📤 Export Limit"
                })
            }),
            description_placeholders={
                "info": "Choose a section to configure"
            }
        )

    async def async_step_charging(self, user_input: dict[str, Any] | None = None):
        """Configure charging schedule."""
        hass = self.hass
        websession = async_get_clientsession(hass)
        oauth_session = config_entry_oauth2_flow.async_get_config_entry_oauth2_session(
            hass, self.config_entry
        )
        api = AsyncConfigEntryAuth(websession, oauth_session)
        system_sn = self.config_entry.data["system_sn"]

        if user_input is not None:
            await api.async_set_charging_schedule(system_sn, {
                "enable": user_input["enable"],
                "start_time_1": user_input["start_time_1"],
                "end_time_1": user_input["end_time_1"],
                "start_time_2": user_input["start_time_2"],
                "end_time_2": user_input["end_time_2"],
                "max_soc": user_input["max_soc"]
            })
            return self.async_create_entry(title="Charging Schedule", data={})

        # Fetch current schedule from API
        charging_schedule = await api.async_get_charging_schedule(system_sn)

        return self.async_show_form(
            step_id="charging",
            data_schema={
                "enable": BooleanSelector(),
                "start_time_1": TimeSelector(),
                "end_time_1": TimeSelector(),
                "start_time_2": TimeSelector(),
                "end_time_2": TimeSelector(),
                "max_soc": NumberSelector(
                    NumberSelectorConfig(
                        min=0,
                        max=100,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="%",
                    )
                ),
            },
            defaults={
                "enable": charging_schedule.get("enable", True),
                "start_time_1": charging_schedule.get("start_time_1", "14:00"),
                "end_time_1": charging_schedule.get("end_time_1", "16:00"),
                "start_time_2": charging_schedule.get("start_time_2", "20:00"),
                "end_time_2": charging_schedule.get("end_time_2", "22:00"),
                "max_soc": charging_schedule.get("max_soc", 95),
            },
            description_placeholders={
                "info": "Configure your battery charging schedule. Time fields must be in HH:MM format."
            }
        )
    
    async def async_step_discharging(self, user_input: dict[str, Any] | None = None):
        """Placeholder for discharging schedule."""
        return self.async_show_form(
            step_id="discharging",
            data_schema={},
            description_placeholders={
                "info": "This section is not yet implemented."
            }
        )

    async def async_step_export(self, user_input: dict[str, Any] | None = None):
        """Placeholder for export limit."""
        return self.async_show_form(
            step_id="export",
            data_schema={},
            description_placeholders={
                "info": "This section is not yet implemented."
            }
        )