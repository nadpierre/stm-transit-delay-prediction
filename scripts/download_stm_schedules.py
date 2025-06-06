from datetime import datetime
from glob import glob
import os
from pathlib import Path
import re
import requests
import zipfile

# Import custom code
from src.constants import ROOT_DIR, DATA_DIR, DOWNLOAD_DIR, logger

url = 'https://www.stm.info/sites/default/files/gtfs/gtfs_stm.zip'

current_time = datetime.now()
current_date = current_time.strftime('%Y-%m-%d')

dest_folder = os.path.join(ROOT_DIR, DATA_DIR, DOWNLOAD_DIR)
zip_file_name = os.path.basename(url)
zip_file_path = os.path.join(dest_folder, zip_file_name)

response = requests.get(url, stream=True)

if response.ok:
  # Add zipfile to data folder
  logger.info('Saving file as %s', zip_file_name)
  with open(zip_file_path, 'wb') as f:
    for chunk in response.iter_content(chunk_size=1024*8):	
      if chunk:
        f.write(chunk)
        f.flush()
        os.fsync(f.fileno())

  # Extract archive
  logger.info('Unzipping %s', zip_file_name)
  with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    zip_ref.extractall(dest_folder)

  # Delete zip file
  logger.info('Deleting %s', zip_file_path)
  os.remove(zip_file_path)

  txt_files = glob(os.path.join(dest_folder, '*.txt'))
  txt_files = [path for path in txt_files if re.search(r'[a-z_]+\.txt', path)]

  for file_path in txt_files:
    stem = Path(file_path).stem
    basename = os.path.basename(file_path)
    if (stem not in ['routes', 'stops', 'stop_times', 'trips', 'calendar']):
      logger.info('Deleting %s', basename)
      os.remove(file_path) # Delete unrelevant text files

else:
  logger.error('Download failed: status code %s\n%s', [response.status_code, response.text])
