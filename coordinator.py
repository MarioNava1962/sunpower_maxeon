from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import AsyncConfigEntryAuth

class SunPowerCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api: AsyncConfigEntryAuth):
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name="SunPower Maxeon",
            update_interval=timedelta(minutes=1),
        )

    async def _async_update_data(self):
        try:
            return await self.api.async_get_systems()
        except Exception as err:
            raise UpdateFailed(f"Failed to fetch data: {err}") from err
