import aiohttp
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers.event import async_track_time_interval

CONF_PLAYER_ID = "player_id"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
SCAN_INTERVAL = timedelta(hours=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PLAYER_ID): cv.positive_int,
    vol.Optional(CONF_USERNAME): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
    vol.Optional("show", default="all"): cv.string
})

STATS_SENSORS = ['matches', 'matches_won', 'matches_lost']

_LOGGER = logging.getLogger(__name__)

def generate_boundary():
    import random
    import string
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))

form_boundary = generate_boundary()



async def login(session, username, password):
    LOGIN_URL = "https://api.leveltech.squashlevels.com/api/classic/menu_login"
    payload = f"""
------WebKitFormBoundary{form_boundary}
Content-Disposition: form-data; name="stay_logged_in"

1
------WebKitFormBoundary{form_boundary}
Content-Disposition: form-data; name="action"

login
------WebKitFormBoundary{form_boundary}
Content-Disposition: form-data; name="referer"

https://app.squashlevels.com/
------WebKitFormBoundary{form_boundary}
Content-Disposition: form-data; name="email"

{username}
------WebKitFormBoundary{form_boundary}
Content-Disposition: form-data; name="password"

Use MD5
------WebKitFormBoundary{form_boundary}
Content-Disposition: form-data; name="md5password"

{hashlib.md5(password.encode()).hexdigest()}
------WebKitFormBoundary{form_boundary}--
"""

    headers = {
        "Accept": "application/json, text/javascript, */*",
        "Connection": "keep-alive",
        "Authorization": "Bearer log.me.out",
        "Origin": "https://app.squashlevels.com",
        "Referer": "https://app.squashlevels.com/",
        "Sec-Fetch-Ua": 'Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Ch-Ua-Platform": "Windows",
        "Sec-Ch-Ua-Mobile": "?0",
        "Content-Type": f"multipart/form-data; boundary=----WebKitFormBoundary{form_boundary}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    async with session.post(LOGIN_URL, data=payload, headers=headers) as response:
        _LOGGER.info(f"Logging in as {username}")
        response_code = response.status
        response_text = await response.text()
        response_headers = response.headers
        _LOGGER.debug(f"Login response code: {response_code}")
        _LOGGER.debug(f"Login response headers: {response_headers}")
        #_LOGGER.debug(f"Login response text: {response_text}")
        return response_text

async def fetch_player_data(session, player_id, show="all"):
    API_URL = f"https://api.leveltech.squashlevels.com/api/classic/player_detail?player={player_id}&format=json&show={show}"
    async with session.get(API_URL) as response:
        return await response.json()

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    player_id = config.get(CONF_PLAYER_ID)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    show = config.get("show")

    _LOGGER.debug(f"Using show setting of {show}")

    async with aiohttp.ClientSession() as session:
        if username and password:
            await login(session, username, password)
        
        data = await fetch_player_data(session, player_id)
        sensors = [
            SquashLevelSensor(data, "level_now", "level", "mdi:racquetball"),
            SquashLevelSensor(data, "damped_level", "level", "mdi:racquetball"),
            SquashLevelSensor(data, "last_match_date", "date", "mdi:calendar"),
            SquashLevelSensor(data, "points_scores", "score", "mdi:racquetball"),
            SquashLevelSensor(data, "games_score", "score", "mdi:racquetball"),
        ]

        status = data['status']
        _LOGGER.info(f"API Status: {status}")
        if status == "good":
            # we are logged in, add extra sensors
            sensors.append(SquashLevelSensor(data, "matches", "integer", "mdi:racquetball"))
            sensors.append(SquashLevelSensor(data, "matches_won", "integer", "mdi:racquetball"))
            sensors.append(SquashLevelSensor(data, "matches_lost", "integer", "mdi:racquetball"))
        async_add_entities(sensors, True)

        async def update_data(_):
            new_data = await fetch_player_data(session, player_id, show)
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
        elif self._sensor_type in STATS_SENSORS:
            self._state = self._data['data']['statistics'][self._sensor_type]
        else:
            self._state = self._data['data']['summary'][self._sensor_type]

    def update_data(self, new_data):
        self._data = new_data
        self._attrs["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.update()
