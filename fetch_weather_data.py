from custom_functions import export_to_csv
from datetime import datetime, UTC
import os
from pathlib import Path
import requests

# Coordinates for Montreal
latitude = 45.5019
longitude = -73.5674

root_dir = Path(__file__).parent.resolve()
csv_path = os.path.join(root_dir, 'data', 'fetched_weather.csv')

# Get current time in UTC
current_time = datetime.now(UTC)
start_time = current_time.strftime('%Y-%m-%dT%H:00') # Round to nearest hour to match API response

# Endpoint
weather_url = (
    f'https://api.open-meteo.com/v1/forecast?'
    f'latitude={latitude}&longitude={longitude}'
    f'&hourly=temperature_2m,precipitation,windspeed_10m,weathercode'
    f'&start_date={current_time.date()}&end_date={current_time.date()}'
    f'&timezone=America%2FToronto'
)

response = requests.get(weather_url)
data = response.json()
weather_list = []

if 'hourly' in data.keys():
  current_hour_index = data['hourly']['time'].index(start_time)
  temperature = data['hourly']['temperature_2m'][current_hour_index]
  precipitation = data['hourly']['precipitation'][current_hour_index]
  windspeed = data['hourly']['windspeed_10m'][current_hour_index]
  weathercode = data['hourly']['weathercode'][current_hour_index]

  weather_list.append({
    'current_time': start_time.isoformat(),
    'temperature': temperature,
    'precipitation': precipitation,
    'windspeed': windspeed,
    'weathercode': weathercode
  })

if len(weather_list) > 0:
  export_to_csv(weather_list, csv_path)
  