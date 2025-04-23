from custom_functions import data_dir, logger, root_dir
from datetime import datetime
from glob import glob
import os
from pathlib import Path
import requests
import zipfile

url = 'https://www.stm.info/sites/default/files/gtfs/gtfs_stm.zip'

current_time = datetime.now()
current_date = current_time.strftime('%Y-%m-%d')

dest_folder = os.path.join(root_dir, data_dir)
zip_file_name = os.path.basename(url)
zip_file_path = os.path.join(dest_folder, zip_file_name)

response = requests.get(url, stream=True)

if response.ok:
  logger.info('Saving file as %s', zip_file_name)

  logger.info('Unzipping %s', zip_file_name)

  # Add zipfile to data folder
  with open(zip_file_path, 'wb') as f:
    for chunk in response.iter_content(chunk_size=1024*8):	
      if chunk:
        f.write(chunk)
        f.flush()
        os.fsync(f.fileno())
  
  # Extract archive
  with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    zip_ref.extractall(dest_folder)

  # Delete zip file
  logger.info('Deleting %s', zip_file_path)
  os.remove(zip_file_path)

  # Delete unrelevant text files
  txt_files = glob(os.path.join(dest_folder, '*.txt'))
  for file_path in txt_files:
    if Path(file_path).stem != 'stop_times':
      os.remove(file_path)
  
  # Add date to stop_times.txt (schedules are updated weekly)
  old_path = os.path.join(dest_folder, 'stop_times.txt')
  new_path = os.path.join(dest_folder, f'stop_times_{current_date}.txt')
  os.rename(old_path, new_path)

else:
  logger.error('Download failed: status code %s\n%s', [response.status_code, response.text])
