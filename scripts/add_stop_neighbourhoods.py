from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import os
import pandas as pd

# Import custom code
from src.constants import ROOT_DIR, DATA_DIR

# Load data
raw_csv_path = os.path.join(ROOT_DIR, DATA_DIR, 'stops_2025-04-30.txt')
stops_df = pd.read_csv(raw_csv_path)

# Keep relevant columns 
stops_df = stops_df.drop(['stop_id', 'stop_url', 'parent_station'], axis=1)

# Rename stop code
stops_df = stops_df.rename(columns={'stop_code': 'stop_id'})

# Use reverse geocoding to add neighbourhoods
def get_neighbourhood(row:pd.Series) -> str:
	location = reverse((row['stop_lat'], row['stop_lon']), language='en', exactly_one=True)

	if location != None:
		address = location.raw['address']
		return address['neighbourhood'] if 'neighbourhood' in address.keys() else None

	return None

geolocator = Nominatim(user_agent='transit_delay_prediction')
reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)
neighbourhoods = stops_df.apply(get_neighbourhood, axis=1)
stops_df.insert(2, 'neighbourhood', neighbourhoods)

# Export data
cleaned_csv_path = os.path.join(ROOT_DIR, DATA_DIR, 'stops_cleaned.csv')
stops_df.to_csv(cleaned_csv_path, index=False)
