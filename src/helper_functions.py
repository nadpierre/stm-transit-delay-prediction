import geopandas as gpd
import os
import pandas as pd
import requests

# Import custom code
from src.constants import MTL_COORDS, ROOT_DIR, DATA_DIR, DOWNLOAD_DIR, LOCAL_TIMEZONE

# Data folders
data_path = os.path.join(ROOT_DIR, DATA_DIR)
download_path = os.path.join(data_path, DOWNLOAD_DIR)

# Data files
routes_path = os.path.join(download_path, 'routes.txt')
trips_path = os.path.join(download_path, 'trips.txt')
stop_times_path = os.path.join(download_path, 'stop_times.txt')
calendar_path = os.path.join(download_path, 'calendar.txt')
stops_path = os.path.join(data_path, 'stops_with_clusters.csv')
avg_delay_path = os.path.join(data_path, 'hist_avg_delays.csv')

# Load data
routes_df = pd.read_csv(routes_path)
trips_df = pd.read_csv(trips_path)
stop_times_df = pd.read_csv(stop_times_path)
stops_df = pd.read_csv(stops_path)
calendar_df = pd.read_csv(calendar_path)
avg_delay_df = pd.read_csv(avg_delay_path)

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

def get_trip_info(route_id:int, direction:str, stop_id:int, chosen_time_local:pd.Timestamp) -> pd.DataFrame:
  trip_data = {}

  trip_result = {
    'next_arrival_time': pd.Timestamp.now(),
    'trip_data' : trip_data
  }

def get_weather_info(arrival_time_utc:pd.Timestamp, forecast:bool=False) -> dict:
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


def parse_gtfs_time(df:pd.DataFrame, date_column:str, time_column:str, unit:str) -> pd.Series:
  '''
  Converts GTFS time string (e.g., '25:30:00') to localized datetime
  based on the arrival or departure time.
  '''
  time_columns = ['hours', 'minutes', 'seconds']
  split_cols = df[time_column].str.split(':', expand=True).apply(pd.to_numeric)
  split_cols.columns = time_columns
  seconds_delta = (split_cols['hours'] * 3600) + (split_cols['minutes'] * 60) + split_cols['seconds']
	
	# Convert datetime to seconds
  if unit == 'ms':# milliseconds
    start_seconds = df[date_column].astype('int64') / 10**3
  elif unit == 'us':# microseconds
    start_seconds = df[date_column].astype('int64') / 10**6
  elif unit == 'ns':# nanoseconds
    start_seconds = df[date_column].astype('int64') / 10**9

	# Add seconds 
  total_seconds = start_seconds + seconds_delta

	# Convert to datetime
  parsed_time = pd.to_datetime(total_seconds, origin='unix', unit='s').dt.tz_localize(LOCAL_TIMEZONE)

  return parsed_time




