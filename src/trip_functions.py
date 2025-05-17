import joblib
import os
import pandas as pd
import random

# Import custom code
from src.constants import ROOT_DIR, DATA_DIR, MODELS_DIR, DOWNLOAD_DIR, LOCAL_TIMEZONE, logger
from src.helper_functions import fetch_weather, parse_gtfs_time, get_route_bearing

# File paths
data_path = os.path.join(ROOT_DIR, DATA_DIR)
download_path = os.path.join(data_path, DOWNLOAD_DIR)
routes_path = os.path.join(download_path, 'routes.txt')
trips_path = os.path.join(download_path, 'trips.txt')
stop_times_path = os.path.join(download_path, 'stop_times.txt')
calendar_path = os.path.join(download_path, 'calendar.txt')
stops_path = os.path.join(data_path, 'stops_with_clusters.csv')
avg_delay_path = os.path.join(data_path, 'hist_avg_delays.csv')
sch_rel_path = os.path.join(ROOT_DIR, MODELS_DIR, 'sch_rel_weights.pkl')

# Load data
routes_df = pd.read_csv(routes_path)
trips_df = pd.read_csv(trips_path)
stop_times_df = pd.read_csv(stop_times_path)
stops_df = pd.read_csv(stops_path)
calendar_df = pd.read_csv(calendar_path, parse_dates=['start_date', 'end_date'], date_format='%Y%m%d')
avg_delay_df = pd.read_csv(avg_delay_path)
sch_rel_weights = joblib.load(sch_rel_path)

# Convert calendar start and end date to local timezone
calendar_df['start_date'] = calendar_df['start_date'].dt.tz_localize(LOCAL_TIMEZONE)
calendar_df['end_date'] = calendar_df['end_date'].dt.tz_localize(LOCAL_TIMEZONE) + pd.Timedelta(days=1)

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
  trip_data = {}

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

  # Add stop cluster
  stop_location_group = float(next_arrival['stop_cluster'])
  trip_data['stop_cluster'] = stop_location_group

  # Get first and last stop coordinates
  origin_lat = current_trip.iloc[0]['stop_lat']
  origin_lon = current_trip.iloc[0]['stop_lon']
  dest_lat = current_trip.iloc[-1]['stop_lat']
  dest_lon = current_trip.iloc[-1]['stop_lon']

  # Add route bearing
  bearing = get_route_bearing(dest_lon, origin_lon, dest_lat, origin_lat)
  trip_data['route_bearing'] = bearing
  
  # Add expected trip duration
  trip_start = current_trip['sch_arrival_time'].min()
  trip_end = current_trip['sch_arrival_time'].max()
  trip_data['exp_trip_duration'] = (trip_end - trip_start) / pd.Timedelta(seconds=1)

  # Add historical average delay
  hour = next_arrival['sch_arrival_time'].hour
  hist_filter = (avg_delay_df['route_id'] == route_id) & (avg_delay_df['stop_id'] == stop_id) & (avg_delay_df['hour'] == hour)
  filtered_avg_delay = avg_delay_df[hist_filter]
  hist_avg_delay = float(filtered_avg_delay['hist_avg_delay'].iloc[0])
  trip_data['hist_avg_delay'] = hist_avg_delay

  # Add arrivals per hour
  arrivals_per_hour = int(next_arrival['arrivals_per_hour'])
  trip_data['arrivals_per_hour'] = arrivals_per_hour

  # Add schedule_relationship one-hot value (at random)
  sch_rel = random.choices([1, 0], weights=sch_rel_weights.values(), k=1)[0]
  trip_data['schedule_relationship_Scheduled'] = sch_rel
 
  return {
    'next_arrival_time': next_arrival_time,
    'trip_data' : trip_data,
    'hist_avg_delay': round(hist_avg_delay / 60),
  }

def get_weather_info(arrival_time_utc:pd.Timestamp, forecast:bool=False) -> dict:
  weather_start_date = arrival_time_utc.strftime('%Y-%m-%d')
  weather_time = arrival_time_utc.round('h').strftime('%Y-%m-%dT%H:%M')
       
  attributes = [
    'cloud_cover',
    'relative_humidity_2m',
    'temperature_2m',
    'wind_direction_10m',
    'wind_speed_10m'
  ]

  weather_list = fetch_weather(weather_start_date, weather_start_date, attributes, forecast=forecast)

  return [item for item in weather_list if item['time'] == weather_time][0]