import logging
import os
from pathlib import Path

# Directories and files
ROOT_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = 'data'
API_DIR = 'api'
DOWNLOAD_DIR = 'download'
MODELS_DIR = 'models'
LOG_FILE = os.path.join(ROOT_DIR, 'stm_api_errors.log')

# Logger
logger = logging.getLogger('stm.delay_prediction')
logging.basicConfig(
  filename=LOG_FILE,
  level=logging.DEBUG,
  format='%(asctime)s %(name)s [%(levelname)s] %(message)s',
  datefmt='%Y-%m-%d %H:%M:%S')

LOCAL_TIMEZONE = 'Canada/Eastern'

MTL_COORDS = {
  'latitude': 45.508888,
  'longitude':  -73.561668
}

SCHEDULE_RELATIONSHIP = {
  0: 'Scheduled',
  1: 'Skipped',
  2: 'NoData',
}

WEATHER_CODES = {
  0: 'Clear sky',
  1: 'Mainly clear',
  2: 'Partly cloudy',
  3: 'Overcast',
  45: 'Fog',
  48: 'Depositing rime fog',
  51: 'Light drizzle',
  53: 'Moderate drizzle',
  55: 'Dense drizzle',
  56: 'Light freezing drizzle',
  57: 'Dense freezing drizzle',
  61: 'Slight rain',
  63: 'Moderate rain',
  65: 'Heavy rain',
  66: 'Light freezing rain',
  67: 'Heavy frizzing rain',
  71: 'Slight snow fall',
  73: 'Moderate snow fall',
  75: 'Heavy snow fall',
  77: 'Snow grains',
  80: 'Slight rain showers',
  81: 'Moderate rain showers',
  82: 'Violent rain showers',
  85: 'Slight show showers',
  86: 'Heavy show showers',
  95: 'Slight or moderate thunderstorm',
  96: 'Thunderstorm with slight hail',
  99: 'Thunderstorm with heavy hail'
}