from custom_functions import data_dir, export_to_csv, fetch_weather, root_dir
from datetime import datetime, timedelta, timezone
import os

csv_path = os.path.join(root_dir, data_dir, 'fetched_historical_weather.csv')

# Get current time in UTC
current_time = datetime.now(timezone.utc)
three_days_before = current_time - timedelta(days=3)
start_date = three_days_before.strftime('%Y-%m-%d')

weather_list = fetch_weather(start_date=start_date, end_date=start_date)

if len(weather_list) > 0:
  export_to_csv(weather_list, csv_path)
  