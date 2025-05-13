import os
import pandas as pd
import requests

# Import custom code
from src.constants import MTL_COORDS, ROOT_DIR, DATA_DIR, DOWNLOAD_DIR

# Data files
download_path = os.path.join(ROOT_DIR, DATA_DIR, DOWNLOAD_DIR)
routes_path = os.path.join(download_path, 'routes.txt')
trips_path = os.path.join(download_path, 'trips.txt')
stop_times_path = os.path.join(download_path, 'stop_times.txt')
stops_path = os.path.join(ROOT_DIR, DATA_DIR, 'stop_clusters.csv')

# Load data
routes_df = pd.read_csv(routes_path)
trips_df = pd.read_csv(trips_path)
stop_times_df = pd.read_csv(stop_times_path)
stops_df = pd.read_csv(stops_path)

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

def get_bus_lines() -> list:
  bus_lines_df = routes_df[routes_df['route_type'] == 3]
  bus_lines_df = bus_lines_df[['route_id', 'route_long_name', 'route_color', 'route_text_color']]
  
  return bus_lines_df.to_dict(orient='records')

def get_bus_directions(bus_line:str) -> list:
  route_id = int(bus_line)
  trip_headsign = trips_df[trips_df['route_id'] == route_id]['trip_headsign']

  # Extract first word
  split = trip_headsign.str.split(expand=True)
  
  # Remove repetitions
  directions_fr = split[0].sort_values().unique().tolist()

  # Translate directions
  directions = []
  for direction in directions_fr:
    data = {}
    data['direction_fr'] = direction
       
    if 'Nord' in direction:
      data['direction_en'] = 'North'
    elif 'Sud' in direction:
      data['direction_en'] = 'South'
    elif 'Ouest' in direction:
      data['direction_en'] = 'West'
    elif 'Est' in direction:
      data['direction_en'] = 'East'
    
    directions.append(data)

  return directions

def get_bus_stops(bus_line:str, direction:str) -> list:
  route_id = int(bus_line)
  trip_id = trips_df[(trips_df['route_id'] == route_id) & (trips_df['trip_headsign'].str.contains(direction))].iloc[0]['trip_id']
  trip_stops_df = stop_times_df[stop_times_df['trip_id'] == trip_id][['stop_id', 'stop_sequence']]
  stops_df2 = stops_df[['stop_id', 'stop_name']]
  merged_stops_df = pd.merge(trip_stops_df, stops_df2, how='inner', on='stop_id')
  
  return merged_stops_df.to_dict(orient='records')