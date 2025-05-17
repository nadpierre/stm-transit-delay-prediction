import math
import os
import pandas as pd
import requests

# Import custom code
from src.constants import MTL_COORDS, LOCAL_TIMEZONE

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

def get_redundant_pairs(df: pd.DataFrame) -> set:
	'''Get diagonal and lower triangular pairs of correlation matrix'''
	pairs_to_drop = set()
	cols = df.columns

	for i in range(df.shape[1]):
		for j in range(i + 1):
			pairs_to_drop.add((cols[i], cols[j]))
	return pairs_to_drop

def get_top_abs_correlations(df):
	corr_list = df.corr().abs().unstack()
	labels_to_drop = get_redundant_pairs(df)
	corr_list = corr_list.drop(labels=labels_to_drop).sort_values(ascending=False)
	return corr_list[corr_list > 0.9]

def get_route_bearing(destination_lon, origin_lon, destination_lat, origin_lat) -> float:
	deltaX = destination_lon - origin_lon
	deltaY = destination_lat - origin_lat
	degrees = math.atan2(deltaX, deltaY) / math.pi * 180

	if degrees < 0:
		bearing = 360 + degrees
	else:
		bearing = degrees
	
	return bearing

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




