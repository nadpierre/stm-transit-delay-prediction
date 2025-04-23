from custom_functions import data_dir, export_to_csv, root_dir
from datetime import datetime, timedelta, UTC
import os
import requests

# Coordinates for Montreal
latitude = 45.5019
longitude = -73.5674

csv_path = os.path.join(root_dir, data_dir, 'fetched_weather.csv')

# Get current time in UTC
current_time = datetime.now(UTC)
three_days_before = current_time - timedelta(days=3)

weather_url = (
    f'https://archive-api.open-meteo.com/v1/archive?'
    f'latitude={latitude}&longitude={longitude}'
    f'&hourly=temperature_2m,precipitation,windspeed_10m,weathercode'
    f'&start_date={three_days_before.date()}&end_date={three_days_before.date()}'
    f'&timezone=America%2FToronto'
)

response = requests.get(weather_url)
data = response.json()

weather_list = []

if 'hourly' in data.keys():
  for i in range(len(data['hourly']['time'])):
    weather_list.append({
      'time': data['hourly']['time'][i],
      'temperature': data['hourly']['temperature_2m'][i],
      'precipitation': data['hourly']['precipitation'][i],
      'windspeed': data['hourly']['windspeed_10m'][i],
      'weathercode': data['hourly']['weathercode'][i]
  })  

if len(weather_list) > 0:
  export_to_csv(weather_list, csv_path)
  