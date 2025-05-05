"""Config flow for SunPower Maxeon."""
from collections.abc import Mapping
from typing import Any
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow, selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from datetime import datetime

from .const import DOMAIN
from .api import AsyncConfigEntryAuth

_LOGGER = logging.getLogger(__name__)


class TimeStrValidator:
    def __call__(self, value: str) -> str:
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError:
            raise vol.Invalid("Time must be in HH:MM format (24-hour)")
        return value


class MaxSoCValidator:
    def __call__(self, value: int) -> int:
        if not 0 <= value <= 100:
            raise vol.Invalid("Max SoC must be between 0 and 100")
        return value



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
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        hass = self.hass

        if user_input is not None:
            # Runtime validation
            for key in ("start_time_1", "end_time_1", "start_time_2", "end_time_2"):
                TimeStrValidator()(user_input[key])  # This calls the __call__ method of TimeStrValidator
            MaxSoCValidator()(user_input["max_soc"])

            # Create API client
            websession = async_get_clientsession(hass)
            oauth_session = config_entry_oauth2_flow.async_get_config_entry_oauth2_session(
                hass, self.config_entry
            )
            api = AsyncConfigEntryAuth(websession, oauth_session)
            system_sn = self.config_entry.data["system_sn"]

            await api.async_set_charging_schedule(system_sn, {
                "enable": user_input["enable"],
                "start_time_1": user_input["start_time_1"],
                "end_time_1": user_input["end_time_1"],
                "start_time_2": user_input["start_time_2"],
                "end_time_2": user_input["end_time_2"],
                "max_soc": user_input["max_soc"]
            })

            # Show persistent notification
            hass.async_create_task(
                hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "SunPower Charging Schedule Updated",
                        "message": (
                            f"Charging schedule updated:\n\n"
                            f"Enabled: {user_input['enable']}\n"
                            f"Start 1: {user_input['start_time_1']} - End 1: {user_input['end_time_1']}\n"
                            f"Start 2: {user_input['start_time_2']} - End 2: {user_input['end_time_2']}\n"
                            f"Max SoC: {user_input['max_soc']}%"
                        ),
                    },
                )
            )

            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("enable", default=True): bool,
                vol.Required("start_time_1", default="14:00"): vol.All(str, TimeStrValidator()),
                vol.Required("end_time_1", default="16:00"): vol.All(str, TimeStrValidator()),
                vol.Required("start_time_2", default="14:00"): vol.All(str, TimeStrValidator()),
                vol.Required("end_time_2", default="16:00"): vol.All(str, TimeStrValidator()),
                vol.Required("max_soc", default=95): vol.All(int, MaxSoCValidator()),
            }),
        )

