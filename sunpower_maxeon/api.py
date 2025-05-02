"""API for SunPower Maxeon bound to Home Assistant OAuth2."""

import logging

from aiohttp import ClientSession

from homeassistant.helpers import config_entry_oauth2_flow

_LOGGER = logging.getLogger(__name__)

class AsyncConfigEntryAuth:
    """Handle authenticated communication with the SunPower Maxeon API."""

    def __init__(
        self,
        websession: ClientSession,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ) -> None:
        """Initialize the API client."""
        self._websession = websession
        self._oauth_session = oauth_session

    async def async_get_access_token(self) -> str:
        """Return a valid OAuth2 access token."""
        await self._oauth_session.async_ensure_token_valid()
        return self._oauth_session.token["access_token"]

    async def async_get_systems(self) -> list:
        """Fetch a list of systems on the site."""
        token = await self.async_get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = "https://api.maxeon.com/v1/systems"

        try:
            async with self._websession.get(url, headers=headers) as resp:
                resp.raise_for_status()
                return await resp.json()
        except Exception as err:
            _LOGGER.error("Failed to fetch systems: %s", err)
            raise
