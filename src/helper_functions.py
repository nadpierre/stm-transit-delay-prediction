import os
import pandas as pd
import requests

# Import custom code
from constants import MTL_COORDS

def export_to_csv(dict_list:list, csv_path:str) -> None:
  df = pd.DataFrame(dict_list)
  if not os.path.isfile(csv_path):
    df.to_csv(csv_path, index=False)
  else:
    df.to_csv(csv_path, index=False, header=False, mode='a')

def fetch_weather(start_date:str, end_date:str, attribute_list:list[str], forecast:bool=False) -> list:
  root_url = 'https://archive-api.open-meteo.com/v1/archive?' \
    if forecast == False else 'https://api.open-meteo.com/v1/forecast?'
  
  attributes = ','.join(attribute_list)
  
  weather_url = (
    f'{root_url}'
    f'latitude={MTL_COORDS["latitude"]}&longitude={MTL_COORDS["longitude"]}'
    f'&hourly={attributes}'
    f'&start_date={start_date}&end_date={end_date}'
    f'&timezone=America%2FToronto'
  )
  
  weather_list = []
  response = requests.get(weather_url)

  if response.ok :
    data = response.json()
    if 'hourly' in data.keys():
      for i in range(len(data['hourly']['time'])):
        weather = {}
        weather['time'] = data['hourly']['time'][i]
        for attribute in attribute_list:
          weather[attribute] = data['hourly'][attribute][i]
        weather_list.append(weather)
        
  return weather_list