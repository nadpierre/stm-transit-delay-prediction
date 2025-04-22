from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv
from google.transit import gtfs_realtime_pb2
import logging
import os
import pandas as pd
import requests
import time
import sys

script_start_time = time.time()

logging.basicConfig(
  filename='stm_api_errors.log',
  level=logging.INFO,
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  datefmt='%Y-%m-%d %H:%M:%S'
)

# Coordinates for Montreal
latitude = 45.5019
longitude = -73.5674

# API KEY
load_dotenv()
API_KEY = os.getenv('STM_API_KEY')

# CSV file path
csv_path = 'data/fetched_stm_and_weather.csv'

# STM trip updates endpoint
url = 'https://api.stm.info/pub/od/gtfs-rt/ic/v2/tripUpdates'
headers = {'accept': 'application/x-protobuf', 'apiKey': API_KEY}

# Fetch weather data from Open-Meteo API
def fetch_weather_data(hour:datetime) -> dict:
  result = {
    'temperature': None,
    'precipitation': None,
    'windspeed': None,
    'weathercode': None
  }

  start_time = hour.strftime('%Y-%m-%dT%H:00') # Round to nearest hour to match API response 

  weather_url = (
      f'https://api.open-meteo.com/v1/forecast?'
      f'latitude={latitude}&longitude={longitude}'
      f'&hourly=temperature_2m,precipitation,windspeed_10m,weathercode'
      f'&start_date={hour.date()}&end_date={hour.date()}'
      f'&timezone=America%2FToronto'
  )

  response = requests.get(weather_url)
  data = response.json()

  if 'hourly' in data.keys():
    current_hour_index = data['hourly']['time'].index(start_time)
    temperature = data['hourly']['temperature_2m'][current_hour_index]
    precipitation = data['hourly']['precipitation'][current_hour_index]
    windspeed = data['hourly']['windspeed_10m'][current_hour_index]
    weathercode = data['hourly']['weathercode'][current_hour_index]

    result['temperature'] = temperature
    result['precipitation'] = precipitation
    result['windspeed'] = windspeed
    result['weathercode'] = weathercode

  return result

# Do 5 attempts in case of connection timeout error
max_retries = 5
backoff_factor = 2
timeout = 10

for attempt in range(1, max_retries + 1):
  try:
    response = requests.get(url=url, headers=headers, timeout=timeout)
    response.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    for entity in feed.entity:
      trip = entity.trip_update.trip
      
      trip_updates = []

      for stop_time_update in entity.trip_update.stop_time_update:

        # Get timestamp and convert to datetime
        timestamp = stop_time_update.arrival.time
        trip_time = datetime.fromtimestamp(timestamp, UTC)

        # Fetch weather for the current hour
        weather_data = fetch_weather_data(trip_time)
      
        # Store the trip update and weather data in the list
        trip_updates.append({
            'trip_id': trip.trip_id,
            'route_id': trip.route_id,
            'start_date': trip.start_date,
            'stop_id': stop_time_update.stop_id,
            'arrival_time': stop_time_update.arrival.time, # planned time
            'departure_time': stop_time_update.departure.time, # actual time
            'schedule_relationship': stop_time_update.schedule_relationship,
            **weather_data  # Merged weather data
        })
      
      # Convert list to DataFrame
      df = pd.DataFrame(trip_updates)
      # Export to CSV
      if not os.path.isfile(csv_path):
        df.to_csv(csv_path, index=False)
      else:
        df.to_csv(csv_path, index=False, header=False, mode='a')
    
    break # exit of loop if attempt is successful
  except requests.exceptions.RequestException as e:
    wait = backoff_factor ** attempt
    logging.error(f'Attempt {attempt} failed: {e}. Retrying in {wait} seconds...')
    time.sleep(wait)
else:
  logging.error('All retry attempts failed. Consider logging the error or alerting the system administrator.')

logging.info(f'Execution time: {time.time() - script_start_time} seconds')