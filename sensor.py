import aiohttp
import asyncio
from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers.event import async_track_time_interval

CONF_PLAYER_ID = "player_id"
SCAN_INTERVAL = timedelta(hours=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PLAYER_ID): cv.positive_int,
})

async def fetch_player_data(player_id):
    API_URL = f"https://api.leveltech.squashlevels.com/api/classic/player_detail?player={player_id}&format=json"
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            return await response.json()

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    player_id = config.get(CONF_PLAYER_ID)
    data = await fetch_player_data(player_id)
    sensors = [
        SquashLevelSensor(data, "level_now", "level", "mdi:racquetball"),
        SquashLevelSensor(data, "damped_level", "level", "mdi:racquetball"),
        SquashLevelSensor(data, "last_match_date", "date", "mdi:calendar"),
        SquashLevelSensor(data, "points_scores", "score", "mdi:racquetball"),
        SquashLevelSensor(data, "games_score", "score", "mdi:racquetball"),
    ]
    async_add_entities(sensors, True)

    async def update_data(_):
        new_data = await fetch_player_data(player_id)
        for sensor in sensors:
            sensor.update_data(new_data)
            sensor.async_schedule_update_ha_state(True)

    async_track_time_interval(hass, update_data, SCAN_INTERVAL)

class SquashLevelSensor(Entity):
    def __init__(self, data, sensor_type, unit_of_measurement, icon=None):
        self._data = data
        self._sensor_type = sensor_type
        self._state = None
        self._attrs = {
            "unit_of_measurement": unit_of_measurement,
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        if icon:
            self._attr_icon = icon
        self.update()

    @property
    def name(self):
        sensor_name = self._sensor_type
        if sensor_name == "points_scores" or sensor_name == "games_score":
            sensor_name = f"last_{sensor_name}"
        return f"{self.get_player_name()} SquashLevels {sensor_name.replace('_', ' ').title()}"

    @property
    def extra_state_attributes(self):
        return self._attrs

    @property
    def state(self):
        return self._state

    @property
    def unique_id(self):
        return f"{self.get_player_id()}_{self._sensor_type}"

    def get_player_id(self):
        return self._data['data']['summary']['playerid']

    def get_player_name(self):
        return self._data['data']['summary']['player_name']

    def update(self):
        if self._sensor_type == "last_match_date":
            self._state = datetime.fromtimestamp(self._data['data']['summary']['last_dateint']).strftime('%Y-%m-%d')
        elif self._sensor_type == "points_scores" or self._sensor_type == "games_score":
            self._state = self._data['data']['matches'][0][self._sensor_type]
        else:
            self._state = self._data['data']['summary'][self._sensor_type]

    def update_data(self, new_data):
        self._data = new_data
        self._attrs["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.update()
