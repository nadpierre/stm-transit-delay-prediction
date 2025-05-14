from datetime import timezone
from flask import Flask, request, jsonify, render_template, Response
import joblib
import json
import numpy as np
import os
import pandas as pd
import pytz

# Import custom code
from src.constants import LOCAL_TIMEZONE, ROOT_DIR, MODELS_DIR
from src.helper_functions import get_bus_lines, get_bus_directions, get_bus_stops, fetch_hourly_weather

app = Flask(__name__)

# File paths
model_path = os.path.join(ROOT_DIR, MODELS_DIR, 'regression_model.pkl')
scaler_path = os.path.join(ROOT_DIR, MODELS_DIR, 'scaler_coords.pkl')
best_feat_path = os.path.join(ROOT_DIR, MODELS_DIR, 'best_features.pkl')

# Load data
model = joblib.load(model_path)
scaler = joblib.load(scaler_path)
best_features = joblib.load(best_feat_path)

@app.route('/')
def home():
  bus_lines = get_bus_lines()
  return render_template('index.html', bus_lines=bus_lines)

@app.route('/get-directions', methods=['POST'])
def get_directions():
    bus_line = request.json.get('bus_line')
    directions = jsonify(get_bus_directions(bus_line))
    return directions

@app.route('/get-stops', methods=['POST'])
def get_stops():
    bus_line = request.json.get('bus_line')
    direction = request.json.get('direction')
    stops = get_bus_stops(bus_line, direction)
    return jsonify(stops)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get data from form
        route_id = int(request.form['bus-line'])
        direction = request.form['direction']
        stop_id = int(request.form['stop'])
        arrival_time_str = request.form['expected_arrival']

        # Format arrival date
        arrival_time_local = pd.Timestamp(arrival_time_str, tz=LOCAL_TIMEZONE)
        arrival_time_utc = arrival_time_local.tz_convert(tz=timezone.utc)

        # Get dates
        now_utc = pd.Timestamp.utcnow()
        three_days_before = now_utc - pd.Timedelta(days=3)
        two_weeks_later = now_utc + pd.Timedelta(weeks=2)

        weather = {}
        if arrival_time_utc <= three_days_before:
            weather = fetch_hourly_weather(arrival_time_utc)
        elif arrival_time_utc <= two_weeks_later:
            weather = fetch_hourly_weather(arrival_time_utc, forecast=True)
        else:
            error = {
                'message': 'The date should not be later than 2 weeks from now.'
            }
            return Response(json.dumps(error), status=400, content_type='application/json')

        # Create matrix
        input_df= pd.DataFrame(columns=best_features)  
       
        for attr in weather.keys():
            input_df.iloc[0, attr] = weather[attr]

        # TODO: get other features that are not in form

        # Build matrix
        data = {
            'exp_trip_duration': [3600],
            #'relative_humidity_2m': [60],
            #'wind_direction_10m': [140],
            #'precipitation': [0],
            'time_of_day_morning': [0],
            'hist_avg_delay': [300],
            'route_direction_South': [0],
            #'wind_speed_10m': [10],
            'frequency_normal': [1],
            'time_of_day_evening': [0],
            'stop_location_group': [2],
            'is_peak_hour': [1],
            'trip_phase_middle': [0],
            'frequency_very_rare': [0],
            'route_direction_North': [0],
            'route_direction_West': [1],
            'frequency_rare': [0],
            #'temperature_2m': [24.3],
            'stop_distance': [400],
            #'cloud_cover': [0],
            'trip_phase_start': [0]
        }
        input_matrix = pd.DataFrame(data)

        # Make prediction
        prediction = model.predict(input_matrix)[0]
        predicted_time = arrival_time_local + pd.Timedelta(seconds=prediction)
        rounded_time = predicted_time.round('min')

        result = {}
        result['exp_arrival_time'] = arrival_time_local.strftime('%Y-%m-%d %H:%M')
        result['predicted_time'] = rounded_time.strftime('%Y-%m-%d %H:%M')
        if rounded_time < arrival_time_local:
            result['status'] = 'Early'
        elif rounded_time > arrival_time_local:
            result['status'] = 'Late'
        else:
            result['status'] = 'OnTime'

        return jsonify(result)
    except Exception as error:
        return jsonify(error)
  
if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
