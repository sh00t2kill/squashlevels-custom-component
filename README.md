# Home Assistant SquashLevels Integration

This custom integration for Home Assistant fetches data from the SquashLevels API and creates sensors for `level_now`, `damped_level`, the date of your last match, `points_scores`, and `games_score`.

## Installation

1. Copy the `squashlevels` directory to your Home Assistant `custom_components` directory.

```
custom_components/
└── squashlevels/
    ├── __init__.py
    └── sensor.py
    └── manifest.json
```

2. Add the following configuration to your `configuration.yaml` file:
username and password are optional, however if you add them additional sensors are added.
show is also optional. By default the component pulls all available data. Valid options for show are:
```
last6m
last10
season
year
last12m
last24m
last5y
last10y
```

```yaml
sensor:
  - platform: squashlevels
    player_id: YOUR_PLAYER_ID
    username: <your email>
    password: <your password>
    show: <value>
```

Replace `YOUR_PLAYER_ID` etc with your actual player ID and details.

## Configuration

- `player_id` (Required): The player ID for which you want to fetch data.

## Sensors

The integration creates the following sensors:

- `sensor.<player_name>_squashlevels_level_now`: Current level of the player.
- `sensor.<player_name>_squashlevels_damped_level`: Damped level of the player.
- `sensor.<player_name>_squashlevels_last_match_date`: Date of the last match.
- `sensor.<player_name>_squashlevels_last_points_scores`: Points scores of the last match.
- `sensor.<player_name>_squashlevels_last_games_score`: Games score of the last match.
- `sensor.<player_name>_squashlevels_matches`: Total matches found for the configured show period
- `sensor.<player_name>_squashlevels_matches_won`: Matches Won
- `sensor.<player_name>_squashlevels_matches_lost`: Matches Lost

## Updating Data

The data is refreshed from the API endpoint every hour.

## Example

Here is an example of how the sensors might look in your Home Assistant UI:

```yaml
sensor:
  - platform: squashlevels
    player_id: 11111111
```

