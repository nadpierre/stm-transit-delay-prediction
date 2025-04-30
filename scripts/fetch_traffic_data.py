from custom_functions import data_dir, export_to_csv, root_dir
from dotenv import load_dotenv
import os
import requests

csv_path = os.path.join(root_dir, data_dir, 'fetched_traffic.csv')

TOMTOM_VERSION_NUMBER = 5

MTL_BBOX = {
   'minLon': -73.9741567,
   'minLat': 45.4100756,
   'maxLon': -73.4742952,
   'maxLat': 45.7047897
}

# API KEY
load_dotenv()
API_KEY = os.getenv('TOMTOM_API_KEY')

headers = {'accept': 'application/json'}

url = (
    f'https://api.tomtom.com'
    f'/traffic/services/{TOMTOM_VERSION_NUMBER}/incidentDetails?'
    f'key={API_KEY}&bbox={MTL_BBOX['minLon']},{MTL_BBOX['minLat']},{MTL_BBOX['maxLon']},{MTL_BBOX['maxLat']}'
    f'&fields=%7Bincidents%7Bgeometry%7Bcoordinates%7D%2Cproperties%7BiconCategory%2CstartTime%2CendTime%2Clength%2CmagnitudeOfDelay%2Cdelay%2ClastReportTime%7D%7D%7D'
    f'&language=en-US'
    f'&categoryFilter=0%2C1%2C2%2C3%2C4%2C5%2C6%2C7%2C8%2C9%2C10%2C11%2C14'
    f'&timeValidityFilter=present'
  )

response = requests.get(url=url, headers=headers)

if response.ok:
    data = response.json()
    
    incidents = []

    if 'incidents' in data.keys():
        for incident in data['incidents']:
            category = incident['properties']['iconCategory']
            start_time = incident['properties']['startTime']
            end_time = incident['properties']['endTime']
            length = incident['properties']['length']
            delay = incident['properties']['delay']
            magnitude_of_delay = incident['properties']['magnitudeOfDelay']
            last_report_time = incident['properties']['lastReportTime']
            coordinates = incident['geometry']['coordinates']
            
            for long, lat in coordinates:
              incidents.append({
                  'category': category,
                  'start_time': start_time,
                  'end_time': end_time,
                  'length': length,
                  'delay': delay,
                  'magnitude_of_delay': magnitude_of_delay,
                  'last_report_time': last_report_time,
                  'latitude': lat,
                  'longitude': long
                })
    
    if len(incidents) > 0:
      export_to_csv(incidents, csv_path)
            


