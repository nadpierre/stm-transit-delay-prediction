import logging
import os
import pandas as pd
from pathlib import Path
import requests

DELAY_CLASS = {
  0: 'Early',
  1: 'On Time',
  2: 'Late'
}

LOCAL_TIMEZONE = 'Canada/Eastern'

MTL_COORDS = {
  'latitude': 45.508888,
  'longitude':  -73.561668
}

SCHEDULE_RELATIONSHIP = {
  0: 'Scheduled',
  1: 'Skipped',
  2: 'No Data',
}

root_dir = Path(__file__).parent.parent.resolve()
data_dir = 'data'
api_dir = 'api'
download_dir = 'download'
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
    f'latitude={MTL_COORDS["latitude"]}&longitude={MTL_COORDS["longitude"]}'
    f'&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,precipitation,pressure_msl,visibility,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m'
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
          'relative_humidity': data['hourly']['relative_humidity_2m'][i],
          'dew_point':  data['hourly']['dew_point_2m'][i],
          'precipitation': data['hourly']['precipitation'][i],
          'pressure': data['hourly']['pressure_msl'][i],
          'visibility': data['hourly']['visibility'][i],
          'cloud_cover': data['hourly']['cloud_cover'][i],
          'windspeed': data['hourly']['wind_speed_10m'][i],
          'wind_direction': data['hourly']['wind_direction_10m'][i],
          'wind_gusts': data['hourly']['wind_gusts_10m'][i]
      })
        
  return weather_list