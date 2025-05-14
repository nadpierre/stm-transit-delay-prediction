import os
import pandas as pd
import requests

# Import custom code
from src.constants import MTL_COORDS, ROOT_DIR, DATA_DIR, DOWNLOAD_DIR, LOCAL_TIMEZONE

# Data files
download_path = os.path.join(ROOT_DIR, DATA_DIR, DOWNLOAD_DIR)
routes_path = os.path.join(download_path, 'routes.txt')
trips_path = os.path.join(download_path, 'trips.txt')
stop_times_path = os.path.join(download_path, 'stop_times.txt')
calendar_path = os.path.join(download_path, 'calendar.txt')
stops_path = os.path.join(ROOT_DIR, DATA_DIR, 'stops_with_clusters.csv')

# Load data
routes_df = pd.read_csv(routes_path)
trips_df = pd.read_csv(trips_path)
stop_times_df = pd.read_csv(stop_times_path)
stops_df = pd.read_csv(stops_path)
calendar_df = pd.read_csv(calendar_path)

def export_to_csv(dict_list:list, csv_path:str) -> None:
  df = pd.DataFrame(dict_list)
  if not os.path.isfile(csv_path):
    df.to_csv(csv_path, index=False)
  else:
    df.to_csv(csv_path, index=False, header=False, mode='a')

def fetch_hourly_weather(arrival_time_utc:pd.Timestamp, forecast:bool=False) -> dict:
  weather_start_date = arrival_time_utc.strftime('%Y-%m-%d')
  weather_time = arrival_time_utc.round('h').strftime('%Y-%m-%dT%H:%M')
       
  attributes = [
    'relative_humidity_2m',
    'wind_direction_10m',
    'precipitation',
    'wind_speed_10m',
    'temperature_2m',
    'cloud_cover'
  ]

  weather_list = fetch_weather(weather_start_date, weather_start_date, attributes, forecast=forecast)

  return [item for item in weather_list if item['time'] == weather_time][0]

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

def get_trip_info(route_id:int, direction:str, stop_id:int, arrival_time_local:pd.Timestamp) -> pd.DataFrame:
  day_of_week = arrival_time_local.day_of_week
  calendar_df['start_date_dt'] = pd.to_datetime(calendar_df['start_date'], format='%Y%m%d')
  calendar_df['end_date_dt'] = pd.to_datetime(calendar_df['end_date'], format='%Y%m%d')
  day_mask = False

  match day_of_week:
    case 0:
      day_mask = calendar_df['monday'] == 1
    case 1:
      day_mask = calendar_df['tuesday'] == 1
    case 2:
      day_mask = calendar_df['wednesday'] == 1
    case 3:
      day_mask = calendar_df['thursday'] == 1
    case 4:
      day_mask = calendar_df['friday'] == 1
    case 5:
      day_mask = calendar_df['saturday'] == 1
    case 6:
      day_mask = calendar_df['sunday'] == 1
    
  date_mask = (arrival_time_local >= calendar_df['start_date_dt']) & (arrival_time_local <= calendar_df['end_date_dt'])
  filtered_calendar = calendar_df[calendar_df[day_mask & date_mask]]




