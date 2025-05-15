import geopandas as gpd
import os
import pandas as pd
import requests

# Import custom code
from src.constants import MTL_COORDS, ROOT_DIR, DATA_DIR, DOWNLOAD_DIR, LOCAL_TIMEZONE, logger

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
calendar_df = pd.read_csv(calendar_path, parse_dates=['start_date', 'end_date'], date_format='%Y%m%d')
avg_delay_df = pd.read_csv(avg_delay_path)

# Convert calendar start and end date to local timezone
calendar_df['start_date'] = calendar_df['start_date'].dt.tz_localize(LOCAL_TIMEZONE)
calendar_df['end_date'] = calendar_df['end_date'].dt.tz_localize(LOCAL_TIMEZONE) + pd.Timedelta(days=1)

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

  directions_fr = trip_headsign.sort_values().unique().tolist()
  
  # Translate directions
  directions = []
  for direction in directions_fr:
    data = {}
    data['direction_fr'] = direction
       
    if 'Nord' in direction:
      data['direction_en'] = direction.replace('Nord', 'North')
    elif 'Sud' in direction:
      data['direction_en'] = direction.replace('Sud', 'South')
    elif 'Ouest' in direction:
      data['direction_en'] = direction.replace('Ouest', 'West')
    elif 'Est' in direction:
      data['direction_en'] = direction.replace('Est', 'East')
    
    directions.append(data)

  return directions

def get_bus_stops(bus_line:str, direction:str) -> list:
  route_id = int(bus_line)
  trip_id = trips_df[(trips_df['route_id'] == route_id) & (trips_df['trip_headsign'] == direction)].iloc[0]['trip_id']
  trip_stops_df = stop_times_df[stop_times_df['trip_id'] == trip_id][['stop_id', 'stop_sequence']]
  stops_df_reduced = stops_df[['stop_id', 'stop_name']]
  merged_stops_df = pd.merge(trip_stops_df, stops_df_reduced, how='inner', on='stop_id')
  
  return merged_stops_df.to_dict(orient='records')

def get_trip_info(route_id:int, direction:str, stop_id:int, chosen_time_local:pd.Timestamp) -> dict:
  logger.debug('Chosen date: %s', chosen_time_local)
  trip_data = {}

  # Add direction one-hot features
  if 'Nord' in direction:
    trip_data['route_direction_South'] = 0
    trip_data['route_direction_North'] = 1
    trip_data['route_direction_West'] = 0
  elif 'Sud' in direction:
    trip_data['route_direction_South'] = 1
    trip_data['route_direction_North'] = 0
    trip_data['route_direction_West'] = 0
  elif 'Ouest' in direction:
    trip_data['route_direction_South'] = 0
    trip_data['route_direction_North'] = 0
    trip_data['route_direction_West'] = 1
  else:
    trip_data['route_direction_South'] = 0
    trip_data['route_direction_North'] = 0
    trip_data['route_direction_West'] = 0

  # Create day of week filters
  day_mask = False
  day_of_week = chosen_time_local.day_of_week
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
  
  # Filter calendar
  date_mask = (chosen_time_local >= calendar_df['start_date']) & (chosen_time_local <= calendar_df['end_date'])
  filtered_calendar = calendar_df[day_mask & date_mask]
  service_ids = filtered_calendar['service_id'].unique().tolist()

  # Filter trips
  filtered_trips_df = trips_df[trips_df['service_id'].isin(service_ids)]

  # Merge stop times with trips
  merged_stop_times = pd.merge(left=stop_times_df, right=filtered_trips_df, how='inner', on='trip_id')

  # Add chosen time and start date
  merged_stop_times['chosen_time'] = chosen_time_local
  merged_stop_times['start_date'] = pd.to_datetime(merged_stop_times['chosen_time'].dt.date)

  # Parse scheduled arrival time
  merged_stop_times['sch_arrival_time'] = parse_gtfs_time(merged_stop_times, 'start_date', 'arrival_time', unit='ns')

  # Add arrival hour
  merged_stop_times['arrival_hour'] = merged_stop_times['sch_arrival_time'].dt.floor('h')

  # Merge stops
  scheduled_trips_df = pd.merge(left=merged_stop_times, right=stops_df, how='left', on='stop_id')

  # Filter route_id and direction
  trip_mask = (scheduled_trips_df['route_id'] == route_id) & (scheduled_trips_df['trip_headsign'] == direction)
  filtered_schedule_df = scheduled_trips_df[trip_mask]

  # Filter by stop_id
  filtered_by_stop_df = filtered_schedule_df[filtered_schedule_df['stop_id'] == stop_id]
  filtered_by_stop_df = filtered_by_stop_df.sort_values('sch_arrival_time')

  # Add hourly frequency
  filtered_by_stop_df['arrivals_per_hour'] = filtered_by_stop_df.groupby('arrival_hour').transform('size')

  # Get arrivals after chosen time
  next_arrivals_filter = filtered_by_stop_df['sch_arrival_time'] >= filtered_by_stop_df['chosen_time']
  next_arrivals = filtered_by_stop_df[next_arrivals_filter].sort_values('sch_arrival_time')

  # Get next arrival
  next_arrival = next_arrivals.head(1).squeeze()
  next_trip_id = int(next_arrival['trip_id'])
  next_arrival_time = next_arrival['sch_arrival_time']

  # Get current trip
  current_trip = filtered_schedule_df[filtered_schedule_df['trip_id'] == next_trip_id].sort_values('stop_sequence')

  # Get time of day one-hot features
  hour = next_arrival_time.hour
  if hour < 6:
    trip_data['time_of_day_morning'] = 0
    trip_data['time_of_day_evening'] = 0
  elif hour < 12:
    trip_data['time_of_day_morning'] = 1
    trip_data['time_of_day_evening'] = 0
  elif hour < 18:
    trip_data['time_of_day_morning'] = 0
    trip_data['time_of_day_evening'] = 0
  else:
    trip_data['time_of_day_morning'] = 0
    trip_data['time_of_day_evening'] = 1
  
  # Get peak hour one-hot feature
  day_of_week = next_arrival_time.day_of_week
  trip_data['is_peak_hour'] = int((day_of_week not in [5, 6]) & (hour in [6, 7, 8, 9, 15, 16, 17, 18]))

  # Get previous coordinates
  current_trip['prev_lat'] = current_trip['stop_lat'].shift(1)
  current_trip['prev_lon'] = current_trip['stop_lon'].shift(1)

  # Create GeoDataFrames for previous and current stop
  gdf1 = gpd.GeoDataFrame(
    current_trip[['prev_lon', 'prev_lat']],
    geometry=gpd.points_from_xy(current_trip['prev_lon'], current_trip['prev_lat']),
    crs='EPSG:4326' # WGS84 (sea level)
  ).to_crs(epsg=3857) # Convert to metric

  gdf2 = gpd.GeoDataFrame(
    current_trip[['stop_lon', 'stop_lat']],
    geometry=gpd.points_from_xy(current_trip['stop_lon'], current_trip['stop_lat']),
    crs='EPSG:4326'
  ).to_crs(epsg=3857)

  # Calculate distance from previous stop
  current_trip['stop_distance'] = gdf1.distance(gdf2)
  current_trip['stop_distance'] = current_trip['stop_distance'].fillna(0)

  # Get trip progress
  current_trip['trip_progress'] = current_trip['stop_sequence'] / len(current_trip)

  # Add stop distance
  current_stop = current_trip[current_trip['stop_id'] == stop_id].squeeze()
  trip_data['stop_distance'] = float(current_stop['stop_distance'])
  
  # Get one-hot features from trip progress
  trip_progress = float(current_stop['trip_progress'])
  if trip_progress < 0.33:
    trip_data['trip_phase_middle'] = 0
    trip_data['trip_phase_start'] = 1
  elif trip_progress < 0.67:
    trip_data['trip_phase_middle'] = 1
    trip_data['trip_phase_start'] = 0
  else:
    trip_data['trip_phase_middle'] = 0
    trip_data['trip_phase_start'] = 0

  # Add expected trip duration
  trip_start = current_trip['sch_arrival_time'].min()
  trip_end = current_trip['sch_arrival_time'].max()
  trip_data['exp_trip_duration'] = (trip_end - trip_start) / pd.Timedelta(seconds=1)

  # Add historical average delay
  hist_filter = (avg_delay_df['route_id'] == route_id) & (avg_delay_df['stop_id'] == stop_id) & (avg_delay_df['hour'] == hour)
  filtered_avg_delay = avg_delay_df[hist_filter]
  hist_avg_delay = float(filtered_avg_delay['hist_avg_delay'].iloc[0])
  trip_data['hist_avg_delay'] = hist_avg_delay

  # Add one-hot frequency attributes from frequency
  frequency = int(next_arrival['arrivals_per_hour'])
  if frequency in [1, 2]:
    trip_data['frequency_normal'] = 0
    trip_data['frequency_very_rare'] = 1
    trip_data['frequency_rare'] = 0
  elif frequency in [3, 4]:
    trip_data['frequency_normal'] = 0
    trip_data['frequency_very_rare'] = 0
    trip_data['frequency_rare'] = 1
  elif frequency in [5, 6]:
    trip_data['frequency_normal'] = 1
    trip_data['frequency_very_rare'] = 0
    trip_data['frequency_rare'] = 0
  else:
    trip_data['frequency_normal'] = 0
    trip_data['frequency_very_rare'] = 0
    trip_data['frequency_rare'] = 0

  # Add stop location group
  stop_location_group = float(next_arrival['stop_location_group'])
  trip_data['stop_location_group'] = stop_location_group
 
  return {
    'next_arrival_time': next_arrival_time,
    'trip_data' : trip_data,
    'hist_avg_delay': round(hist_avg_delay / 60),
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




