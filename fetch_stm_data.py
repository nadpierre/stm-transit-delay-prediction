from custom_functions import export_to_csv
from datetime import datetime, UTC
from dotenv import load_dotenv
from google.transit import gtfs_realtime_pb2
import logging
import os
from pathlib import Path
import requests
import time

script_start_time = time.time()

root_dir = Path(__file__).parent.resolve()
log_file = os.path.join(root_dir, 'stm_api_errors.log')
csv_path = os.path.join(root_dir, 'data', 'fetched_stm.csv')

# Logger
logger = logging.getLogger('stm.delay_prediction')
logging.basicConfig(
  filename=log_file,
  level=logging.INFO,
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  datefmt='%Y-%m-%d %H:%M:%S')

# API KEY
load_dotenv()
API_KEY = os.getenv('STM_API_KEY')

# STM trip updates endpoint
url = 'https://api.stm.info/pub/od/gtfs-rt/ic/v2/tripUpdates'
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

    for entity in feed.entity:
      trip = entity.trip_update.trip
      
      trip_updates = []

      for stop_time_update in entity.trip_update.stop_time_update:

        # Get timestamp and convert to datetime
        timestamp = stop_time_update.arrival.time
        trip_time = datetime.fromtimestamp(timestamp, UTC)
        current_time = datetime.now(UTC)
      
        # Store the trip update and weather data in the list
        trip_updates.append({
            'current_time': current_time.isoformat(),
            'trip_id': trip.trip_id,
            'route_id': trip.route_id,
            'start_date': trip.start_date,
            'stop_id': stop_time_update.stop_id,
            'arrival_time': stop_time_update.arrival.time, # planned time
            'departure_time': stop_time_update.departure.time, # actual time
            'schedule_relationship': stop_time_update.schedule_relationship,
        })
      
      export_to_csv(trip_updates, csv_path)
    
    break # exit loop if attempt is successful
  except requests.exceptions.RequestException as e:
    wait = backoff_factor ** attempt
    logger.error(f'Attempt {attempt} failed: {e}. Retrying in {wait} seconds...')
    time.sleep(wait)
else:
  logger.error('All retry attempts failed. Consider logging the error or alerting the system administrator.')

logger.info(f'Execution time: {time.time() - script_start_time} seconds')