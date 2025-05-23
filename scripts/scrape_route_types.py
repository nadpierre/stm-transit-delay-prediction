from bs4 import BeautifulSoup
import os
import requests

# Import custom code
from src.constants import ROOT_DIR, DATA_DIR
from src.helper_functions import export_to_csv

csv_file = os.path.join(ROOT_DIR, DATA_DIR, 'route_types.csv')

url = 'https://www.stm.info/en/info/networks/bus'

response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

table = soup.find('table', {'class': 'bus-list'})
rows = table.find_all('tr')

bus_list = []

for row in rows:
  route_type = None
  route_id = row.find('span', {'class': 'fam-line-number'}).text

  if row.find('span', {'class': 'family-jour'}):
    route_type = 'Day'
  elif row.find('span', {'class': 'family-freq-toute-journee'}):
    route_type = 'All Day High Frequency'
  elif row.find('span', {'class': 'family-freq-periode-pointe'}):
    route_type = 'Rush Hour High Frequency'
  elif row.find('span', {'class': 'family-nuit'}):
    route_type = 'Night'
  
  bus_list.append({
    'route_id': int(route_id),
    'route_type': route_type
  })

if len(bus_list) > 0:
  export_to_csv(bus_list, csv_file)