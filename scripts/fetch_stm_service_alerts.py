from custom_functions import api_dir, data_dir, root_dir, export_to_csv
from dotenv import load_dotenv
import os
import re
import requests

csv_path = os.path.join(root_dir, data_dir, api_dir, 'fetched_stm_service_alerts.csv')

# API KEY
load_dotenv()
API_KEY = os.getenv('STM_API_KEY')

url = 'https://api.stm.info/pub/od/i3/v2/messages/etatservice'
headers = {'accept': 'application/json', 'apiKey': API_KEY}

response = requests.get(url=url, headers=headers)

data = response.json()

alerts = []
for alert in data['alerts']:
  start_date = alert['active_periods']['start']
  end_date = alert['active_periods']['end']
  route_id = None
  message = alert['description_texts'][1]['text']
 
  if message != 'Normal métro service':
    stop_ids = []
    for entity in alert['informed_entities']:
      if 'route_short_name' in entity.keys():
          route_id = entity['route_short_name']
      
      if 'stop_code' in entity.keys():
          stop_id = entity['stop_code']
          stop_ids.append(stop_id)

    if len(stop_ids) == 0:
       stop_ids = re.findall(r'\d{5}', message)

    if len(stop_ids) > 0:      
      for id in stop_ids:
          alerts.append({
            'start_date' : start_date,
            'end_date': end_date,
            'route_id': route_id,
            'stop_id': id,
        })
          
if len(alerts) > 0:
  export_to_csv(alerts, csv_path)
