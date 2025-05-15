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
from src.helper_functions import get_bus_lines, get_bus_directions, get_bus_stops, get_weather_info, get_trip_info

app = Flask(__name__)

# File paths
model_dir = os.path.join(ROOT_DIR, MODELS_DIR)
model_path = os.path.join(model_dir, 'regression_model.pkl')
scaler_path = os.path.join(model_dir, 'scaler_coords.pkl')
best_feat_path = os.path.join(model_dir, 'best_features.pkl')
min_time_path = os.path.join(model_dir, 'min_time.pkl')

# Load data
model = joblib.load(model_path)
scaler = joblib.load(scaler_path)
best_features = joblib.load(best_feat_path)
min_time_local = joblib.load(min_time_path)

@app.route('/')
def home():
  date_format = '%Y-%m-%dT%H:%M'
  result = {
    'bus_lines': get_bus_lines(),
    'min_time': min_time_local.strftime(date_format),
    'max_time': pd.Timestamp('2025-06-15 23:59:59-0400').strftime(date_format) # end of GTFS schedule
  }
  return render_template('index.html', result=result)

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
        chosen_time_str = request.form['chosen-time']

        # Format arrival date
        chosen_time_local = pd.Timestamp(chosen_time_str, tz=LOCAL_TIMEZONE)
        chosen_time_utc = chosen_time_local.tz_convert(tz=timezone.utc)

        # Get dates
        now_local = pd.Timestamp.now(tz=LOCAL_TIMEZONE)
        now_utc = now_local.tz_convert(tz=timezone.utc)
        three_days_before_utc = now_utc - pd.Timedelta(days=3)
        two_weeks_later_utc = now_utc + pd.Timedelta(weeks=2)
        min_time_utc = min_time_local.tz_convert(tz=timezone.utc)
        two_weeks_later_local = two_weeks_later_utc.tz_convert(tz=LOCAL_TIMEZONE)

        # Fetch weather data
        weather_data = {}
        if (chosen_time_utc < min_time_utc) | (chosen_time_utc > two_weeks_later_utc):
            dt_format = '%Y-%m-%d'
            error = {
                'message': f'The date should not be earlier than {min_time_local.strftime(dt_format)} or later than {two_weeks_later_local.strftime(dt_format)}'
            }
            return Response(json.dumps(error), status=400, content_type='application/json')
        else:
            if chosen_time_utc <= three_days_before_utc:
                weather_data = get_weather_info(chosen_time_utc)
            elif chosen_time_utc <= two_weeks_later_utc:
                weather_data = get_weather_info(chosen_time_utc, forecast=True)
        
        # Get trip data
        trip_result = get_trip_info(route_id, direction, stop_id, chosen_time_local)
        trip_data = trip_result['trip_data']

        # Create input matrix
        merged_data = {**weather_data, **trip_data}

        # TODO: sort keys in alphabetical order and loop through
        input_data = {
            'exp_trip_duration': [merged_data['exp_trip_duration']],
            'relative_humidity_2m': [merged_data['relative_humidity_2m']],
            'wind_direction_10m': [merged_data['wind_direction_10m']],
            'precipitation': [merged_data['precipitation']],
            'time_of_day_morning': [merged_data['time_of_day_morning']],
            'hist_avg_delay': [merged_data['hist_avg_delay']],
            'route_direction_South': [merged_data['route_direction_South']],
            'wind_speed_10m': [merged_data['wind_speed_10m']],
            'frequency_normal': [merged_data['frequency_normal']],
            'time_of_day_evening': [merged_data['time_of_day_evening']],
            'stop_location_group': [merged_data['stop_location_group']],
            'is_peak_hour': [merged_data['is_peak_hour']],
            'trip_phase_middle': [merged_data['trip_phase_middle']],
            'frequency_very_rare': [merged_data['frequency_very_rare']],
            'route_direction_North': [merged_data['route_direction_North']],
            'route_direction_West': [merged_data['route_direction_West']],
            'frequency_rare': [merged_data['frequency_rare']],
            'temperature_2m': [merged_data['temperature_2m']],
            'stop_distance': [merged_data['stop_distance']],
            'cloud_cover': [merged_data['cloud_cover']],
            'trip_phase_start': [merged_data['trip_phase_start']] 
        }

        # Make prediction
        input_df = pd.DataFrame(input_data)
        prediction = model.predict(input_df)[0]
        predicted_time = chosen_time_local + pd.Timedelta(seconds=prediction)
        rounded_time = predicted_time.round('min')

        # Send results
        result = {}
        next_arrival_time = trip_result['next_arrival_time']
        result['next_arrival_time'] = next_arrival_time.strftime('%Y-%m-%d %H:%M')
        result['predicted_time'] = rounded_time.strftime('%Y-%m-%d %H:%M')
        if rounded_time < next_arrival_time:
            result['status'] = 'Early'
        elif rounded_time > next_arrival_time:
            result['status'] = 'Late'
        else:
            result['status'] = 'On Time'

        return jsonify(result)
    except Exception as e:
        message = 'An error has occured.'
        
        if hasattr(e, 'message'):
            message = getattr(e, 'message', repr(e))

        error = {
            'message': message
        }
        return Response(json.dumps(error), status=500, content_type='application/json')
  
if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
