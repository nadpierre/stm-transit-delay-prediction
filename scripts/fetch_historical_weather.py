from datetime import datetime, timedelta, timezone
import os

# Import custom code
from src.constants import ROOT_DIR, DATA_DIR, API_DIR
from src.helper_functions import export_to_csv, fetch_weather

csv_path = os.path.join(ROOT_DIR, DATA_DIR, API_DIR, 'fetched_historical_weather.csv')

# Get current time in UTC
current_time = datetime.now(timezone.utc)
three_days_before = current_time - timedelta(days=3)
start_date = three_days_before.strftime('%Y-%m-%d')

attribute_list = [
  'temperature_2m',
  'relative_humidity_2m',
  'precipitation',
  'pressure_msl',
  'cloud_cover',
  'wind_speed_10m',
  'wind_direction_10m',
]

weather_list = fetch_weather(start_date=start_date, end_date=start_date, attribute_list=attribute_list)

if len(weather_list) > 0:
  export_to_csv(weather_list, csv_path)
  