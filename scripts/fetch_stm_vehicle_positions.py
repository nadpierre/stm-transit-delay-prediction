from custom_functions import api_dir, data_dir, export_to_csv, logger, root_dir
from datetime import datetime, timezone
from dotenv import load_dotenv
from google.transit import gtfs_realtime_pb2
import os
import requests
import time

csv_path = os.path.join(root_dir, data_dir, api_dir, 'fetched_stm_vehicle_positions.csv')

# API KEY
load_dotenv()
API_KEY = os.getenv('STM_API_KEY')

# STM trip updates endpoint
url = 'https://api.stm.info/pub/od/gtfs-rt/ic/v2/vehiclePositions'
headers = {'accept': 'application/x-protobuf', 'apiKey': API_KEY}

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

    positions = []

    for entity in feed.entity:
      current_time = datetime.now(timezone.utc)
      vehicle_id = entity.vehicle.vehicle.id
      trip_id = entity.vehicle.trip.trip_id
      route_id = entity.vehicle.trip.route_id
      start_date = entity.vehicle.trip.start_date
      start_time = entity.vehicle.trip.start_time
      latitude = entity.vehicle.position.latitude
      longitude = entity.vehicle.position.longitude
      bearing = entity.vehicle.position.bearing
      speed = entity.vehicle.position.speed
      stop_sequence = entity.vehicle.current_stop_sequence
      status = entity.vehicle.current_status
      timestamp = entity.vehicle.timestamp
      occupancy_status = entity.vehicle.occupancy_status

      positions.append({
        'current_time': current_time.timestamp(),
        'vehicle_id' : vehicle_id,
        'trip_id': trip_id,
        'route_id': route_id,
        'start_date': start_date,
        'start_time' : start_time,
        'latitude' : latitude,
        'longitude': longitude,
        'bearing': bearing,
        'speed': speed,
        'stop_sequence': stop_sequence,
        'status': status,
        'timestamp': timestamp,
        'occupancy_status': occupancy_status
      })
    
    export_to_csv(positions, csv_path)

    break # exit loop if attempt is successful
  except requests.exceptions.RequestException as e:
    wait = backoff_factor ** attempt
    logger.error(f'Attempt {attempt} failed: {e}. Retrying in {wait} seconds...')
    time.sleep(wait)
else:
  logger.error('All retry attempts failed. Consider logging the error or alerting the system administrator.')
