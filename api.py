import logging
from aiohttp import ClientSession, ClientResponseError
from homeassistant.helpers import config_entry_oauth2_flow

from .const import SYSTEMS, SYSTEM_DETAILS

_LOGGER = logging.getLogger(__name__)


class AsyncConfigEntryAuth:
    """Handle authenticated communication with the SunPower Maxeon API."""

    def __init__(
        self,
        websession: ClientSession,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ) -> None:
        self._websession = websession
        self._oauth_session = oauth_session

    async def async_get_access_token(self) -> str:
        await self._oauth_session.async_ensure_token_valid()
        return self._oauth_session.token["access_token"]

    async def async_get_systems(self) -> dict:
        token = await self.async_get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = "https://api.sunpower.maxeon.com/v1/systems"

        try:
            async with self._websession.get(url, headers=headers) as resp:
                resp.raise_for_status()
                return await resp.json()
        except ClientResponseError as err:
            if err.status == 404:
                _LOGGER.warning("Received 404, returning dummy systems data")
                return {"systems": SYSTEMS.get("systems", [])}
            raise
        except Exception as err:
            _LOGGER.error("Failed to fetch systems: %s", err)
            return {"systems": SYSTEMS.get("systems", [])}

    async def async_get_system_details(self, system_sn: str) -> dict:
        token = await self.async_get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://api.sunpower.maxeon.com/v1/systems/{system_sn}"

        try:
            async with self._websession.get(url, headers=headers) as resp:
                resp.raise_for_status()
                return await resp.json()
        except ClientResponseError as err:
            if err.status == 404:
                _LOGGER.warning(f"System {system_sn} not found, returning dummy details")
                return SYSTEM_DETAILS.get("default", {})
            raise
        except Exception as err:
            _LOGGER.error("Failed to fetch system details: %s", err)
            return SYSTEM_DETAILS.get("default", {})
