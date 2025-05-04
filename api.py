import logging

from aiohttp import ClientSession, ClientResponseError

from homeassistant.helpers import config_entry_oauth2_flow




from .const import SYSTEMS, SYSTEM_DETAILS, POWER_METER, ENERGY_METER



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

        """Ensure the OAuth token is valid and return the access token."""

        await self._oauth_session.async_ensure_token_valid()

        return self._oauth_session.token["access_token"]



    async def async_get_systems(self) -> dict:

        """Fetch list of systems from the SunPower Maxeon API."""

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

        """Fetch system details for a specific system by serial number."""

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



    async def async_get_system_power(self, system_sn: str) -> dict:

        """Fetch system power data from the power meter endpoint."""

        token = await self.async_get_access_token()

        headers = {"Authorization": f"Bearer {token}"}

        url = f"https://api.sunpower.maxeon.com/v1/systems/{system_sn}/power_meter"



        try:

            async with self._websession.get(url, headers=headers) as resp:

                resp.raise_for_status()

                return await resp.json()

        except ClientResponseError as err:

            if err.status == 404:

                _LOGGER.warning(f"Power data for system {system_sn} not found, returning dummy data")

                return POWER_METER

            raise

        except Exception as err:

            _LOGGER.error("Failed to fetch system power data: %s", err)

            return POWER_METER



    async def async_get_system_energy(self, system_sn: str) -> dict:

        """Fetch system energy data from the energy meter endpoint."""

        token = await self.async_get_access_token()

        headers = {"Authorization": f"Bearer {token}"}

        url = f"https://api.sunpower.maxeon.com/v1/systems/{system_sn}/energy_meter"



        try:

            async with self._websession.get(url, headers=headers) as resp:

                resp.raise_for_status()

                return await resp.json()

        except ClientResponseError as err:

            if err.status == 404:

                _LOGGER.warning(f"Energy data for system {system_sn} not found, returning dummy data")

                return ENERGY_METER  # This should be defined similarly to POWER_METER

            raise

        except Exception as err:

            _LOGGER.error("Failed to fetch system energy data: %s", err)

            return ENERGY_METER



    async def get_battery_ups_state(self, system_sn: str) -> dict:

        """Fetch the current UPS battery state (enabled/disabled)."""


        token = await self.async_get_access_token()


        headers = {"Authorization": f"Bearer {token}"}

        url = f"https://api.sunpower.maxeon.com/v1/systems/{system_sn}/battery_ups"


        async with self._websession.get(url, headers=headers) as resp:


            resp.raise_for_status()

            return await resp.json()



    async def set_battery_ups_state(self, system_sn: str, enable: bool) -> None:

        """Set the UPS battery enabled state."""


        token = await self.async_get_access_token()

        headers = {


            "Authorization": f"Bearer {token}",

            "Content-Type": "application/json"

        }


        url = f"https://api.sunpower.maxeon.com/v1/systems/{system_sn}/battery_ups"

        payload = {"enable": enable}


        async with self._websession.put(url, headers=headers, json=payload) as resp:

            resp.raise_for_status()