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
#min_time_local = joblib.load(min_time_path)

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
        chosen_time_str = request.form['chosen-time']

        # Format arrival date
        chosen_time_local = pd.Timestamp(chosen_time_str, tz=LOCAL_TIMEZONE)
        chosen_time_utc = chosen_time_local.tz_convert(tz=timezone.utc)

        # TODO: remove manual timestamp after running notebooks
        min_time_local = pd.Timestamp('2025-05-06 20:35:55-0400')

        # Get dates
        now_local = pd.Timestamp.now(tz=LOCAL_TIMEZONE)
        now_utc = now_local.tz_convert(tz=timezone.utc)
        three_days_before = now_utc - pd.Timedelta(days=3)
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
            if chosen_time_utc <= three_days_before:
                weather_data = get_weather_info(chosen_time_utc)
            elif chosen_time_utc <= two_weeks_later_utc:
                weather_data = get_weather_info(chosen_time_utc, forecast=True)

        # Create matrix
        input_df= pd.DataFrame(columns=best_features)  
       
        # Add weather data
        for attr in weather_data.keys():
            input_df.iloc[0, attr] = weather_data[attr]

        # Add trip data
        trip_result = get_trip_info(route_id, direction, stop_id, chosen_time_local)
        trip_data = trip_result['trip_data']
        for attr in trip_data.keys():
            input_df.iloc[0, attr] = trip_data[attr]

        # Make prediction
        prediction = model.predict(input_df)[0]
        predicted_time = chosen_time_local + pd.Timedelta(seconds=prediction)
        rounded_time = predicted_time.round('min')

        result = {}
        next_arrival_time = trip_result['next_arrival_time']
        result['next_arrival_time'] = next_arrival_time.strftime('%Y-%m-%d %H:%M')
        result['predicted_time'] = rounded_time.strftime('%Y-%m-%d %H:%M')
        if rounded_time < next_arrival_time:
            result['status'] = 'Early'
        elif rounded_time > next_arrival_time:
            result['status'] = 'Late'
        else:
            result['status'] = 'OnTime'

        return jsonify(result)
    except Exception as error:
        return jsonify(error)
  
if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
