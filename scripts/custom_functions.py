import logging
import numpy as np
import os
import pandas as pd
from pathlib import Path
import requests

INCIDENT_CATEGORIES = {
    0: 'Unknown',
    1: 'Accident',
    2: 'Fog',
    3: 'DangerousConditions',
    4: 'Rain',
    5: 'Ice',
    6: 'Jam',
    7: 'LaneClosed',
    8: 'RoadClosed',
    9: 'RoadWorks',
    10: 'Wind',
    11: 'Flooding',
    14: 'BrokenDownVehicle',
    99: None,
}

LOCAL_TIMEZONE = 'Canada/Eastern'

STOP_TYPE = {
  0: 'Regular bus stop',
  1: 'Parent metro station',
  2: 'Bus top near metro'
}

MAGNITUDE_OF_DELAY = {
  0: 'Unknown',
  1: 'Minor',
  2: 'Moderate',
  3: 'Major',
  4: 'Undefined'
}

MTL_COORDS = {
  'latitude': 45.5019,
  'longitude':  -73.5674
}

OCCUPANCY_STATUS = {
  1: 'Empty',
  2: 'Many seats available',
  3: 'Few seats available',
  4: 'Standing room only',
  5: 'Crushed standing room only',
  6: 'Full',
  7: 'Not accepting passengers'
}

WEATHER_CODES = {
  0: 'Clear sky',
  1: 'Mainly clear',
  2: 'Partly cloudy',
  3: 'Overcast',
  45: 'Fog',
  48: 'Depositing rime fog',
  51: 'Light drizzle',
  53: 'Moderate drizzle',
  55: 'Dense drizzle',
  56: 'Light freezing drizzle',
  57: 'Dense freezing drizzle',
  61: 'Slight rain',
  63: 'Moderate rain',
  65: 'Heavy rain',
  66: 'Light freezing rain',
  67: 'Heavy frizzing rain',
  71: 'Slight snow fall',
  73: 'Moderate snow fall',
  75: 'Heavy snow fall',
  77: 'Snow grains',
  80: 'Slight rain showers',
  81: 'Moderate rain showers',
  82: 'Violent rain showers',
  85: 'Slight show showers',
  86: 'Heavy show showers',
  95: 'Slight or moderate thunderstorm',
  96: 'Thunderstorm with slight hail',
  99: 'Thunderstorm with heavy hail'
}

STOP_STATUS = {
  1: 'incoming_at',
  2: 'stopped_at',
  3: 'in_transit_to'
}

root_dir = Path(__file__).parent.parent.resolve()
data_dir = 'data'
log_file = os.path.join(root_dir, 'stm_api_errors.log')

# Logger
logger = logging.getLogger('stm.delay_prediction')
logging.basicConfig(
  filename=log_file,
  level=logging.INFO,
  format='%(asctime)s %(name)s [%(levelname)s] %(message)s',
  datefmt='%Y-%m-%d %H:%M:%S')

def export_to_csv(dict_list:list, csv_path:str) -> None:
  df = pd.DataFrame(dict_list)
  if not os.path.isfile(csv_path):
    df.to_csv(csv_path, index=False)
  else:
    df.to_csv(csv_path, index=False, header=False, mode='a')

def fetch_weather(start_date:str, end_date:str, forecast:bool=False) -> list:
  root_url = 'https://archive-api.open-meteo.com/v1/archive?' \
    if forecast == False else 'https://api.open-meteo.com/v1/forecast?' 
  
  weather_url = (
    f'{root_url}'
    f'latitude={MTL_COORDS['latitude']}&longitude={MTL_COORDS['longitude']}'
    f'&hourly=temperature_2m,precipitation,windspeed_10m,weathercode'
    f'&start_date={start_date}&end_date={end_date}'
    f'&timezone=America%2FToronto'
  )
  
  weather_list = []
  response = requests.get(weather_url)

  if response.ok :
    data = response.json()
    if 'hourly' in data.keys():
      for i in range(len(data['hourly']['time'])):
        weather_list.append({
          'time': data['hourly']['time'][i],
          'temperature': data['hourly']['temperature_2m'][i],
          'precipitation': data['hourly']['precipitation'][i],
          'windspeed': data['hourly']['windspeed_10m'][i],
          'weathercode': data['hourly']['weathercode'][i]
      })
        
  return weather_list