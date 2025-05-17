from datetime import timezone
from flask import Flask, request, jsonify, render_template, Response
import joblib
import json
import os
import pandas as pd
import xgboost as xgb

# Import custom code
from src.constants import LOCAL_TIMEZONE, ROOT_DIR, MODELS_DIR
from src.trip_functions import get_bus_lines, get_bus_directions, get_bus_stops, get_weather_info, get_trip_info

app = Flask(__name__)

# File paths
model_dir = os.path.join(ROOT_DIR, MODELS_DIR)
model_path = os.path.join(model_dir, 'regression_model.pkl')
min_time_path = os.path.join(model_dir, 'min_time.pkl')

# Load data
model = joblib.load(model_path)
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
        route_id = int(request.form['bus_line'])
        direction = request.form['direction']
        stop_id = int(request.form['stop'])
        chosen_time_str = request.form['chosen_time']

        # Format arrival date
        chosen_time_local = pd.Timestamp(chosen_time_str, tz=LOCAL_TIMEZONE)
        chosen_time_utc = chosen_time_local.tz_convert(tz=timezone.utc)

        # Get dates
        now_local = pd.Timestamp.now(tz=LOCAL_TIMEZONE)
        now_utc = now_local.tz_convert(tz=timezone.utc)
        three_days_before_utc = now_utc - pd.Timedelta(days=3)
        two_weeks_later_utc = now_utc + pd.Timedelta(weeks=2) # the weather forecast only goes 2 weeks from now
        min_time_utc = min_time_local.tz_convert(tz=timezone.utc)
        two_weeks_later_local = two_weeks_later_utc.tz_convert(tz=LOCAL_TIMEZONE)

        # Get weather data
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

        # Make prediction
        input_df = get_input_matrix(weather_data, trip_data)
        prediction = model.predict(input_df)[0]
        predicted_time = chosen_time_local + pd.Timedelta(seconds=prediction)
        rounded_predicted_time = predicted_time.round('min')

        # Send results
        result = {}
        next_arrival_time = trip_result['next_arrival_time']
        rounded_next_arrival_time = next_arrival_time.round('min')
        result['next_arrival_time'] = next_arrival_time.strftime('%Y-%m-%d %H:%M')
        result['predicted_time'] = rounded_predicted_time.strftime('%Y-%m-%d %H:%M')
        result['hist_avg_delay'] = trip_result['hist_avg_delay']
        
        if rounded_predicted_time < rounded_next_arrival_time:
            result['status'] = 'Early'
        elif rounded_predicted_time > rounded_next_arrival_time:
            result['status'] = 'Late'
        else:
            result['status'] = 'On Time'

        return jsonify(result)
    except Exception as e:
        # message = 'An error has occured.'
        
        # if hasattr(e, 'message'):
        #     message = getattr(e, 'message', repr(e))

        # error = {
        #     'message': message
        # }
        # return Response(json.dumps(error), status=500, content_type='application/json')
        return jsonify(e)
    
def get_input_matrix(weather_data:dict, trip_data:dict):
    merged_data = {**weather_data, **trip_data}

    input_data = {
        'arrivals_per_hour hist_avg_delay' : [merged_data['arrivals_per_hour'] * merged_data['hist_avg_delay']],
        'arrivals_per_hour route_bearing' : [merged_data['arrivals_per_hour'] * merged_data['route_bearing']],
        'cloud_cover exp_trip_duration' : [merged_data['cloud_cover'] * merged_data['exp_trip_duration']],
        'exp_trip_duration relative_humidity_2m': [merged_data['exp_trip_duration'] * merged_data['relative_humidity_2m']],
        'exp_trip_duration route_bearing' : [merged_data['exp_trip_duration'] * merged_data['route_bearing']],
        'exp_trip_duration schedule_relationship_Scheduled' : [merged_data['exp_trip_duration'] * merged_data['schedule_relationship_Scheduled']],
        'exp_trip_duration temperature_2m' : [merged_data['exp_trip_duration'] * merged_data['temperature_2m']],
        'exp_trip_duration wind_direction_10m' : [merged_data['exp_trip_duration'] * merged_data['wind_direction_10m']],
        'exp_trip_duration wind_speed_10m' : [merged_data['exp_trip_duration'] * merged_data['wind_speed_10m']],
        'hist_avg_delay' : [merged_data['hist_avg_delay']],
        'hist_avg_delay route_bearing' : [merged_data['hist_avg_delay'] * merged_data['route_bearing']],
        'hist_avg_delay wind_direction_10m' : [merged_data['hist_avg_delay'] * merged_data['wind_speed_10m']],
        'hist_avg_delay wind_speed_10m' : [merged_data['hist_avg_delay'] * merged_data['wind_speed_10m']],
        'relative_humidity_2m schedule_relationship_Scheduled' : [merged_data['relative_humidity_2m'] * merged_data['schedule_relationship_Scheduled']],
        'route_bearing' : [merged_data['route_bearing']],
        'route_bearing stop_cluster' : [merged_data['route_bearing'] * merged_data['stop_cluster']],
        'route_bearing temperature_2m' : [merged_data['route_bearing'] * merged_data['temperature_2m']],
        'route_bearing wind_direction_10m' : [merged_data['route_bearing'] * merged_data['wind_direction_10m']],
        'route_bearing wind_speed_10m' : [merged_data['route_bearing'] * merged_data['wind_speed_10m']],
        'schedule_relationship_Scheduled temperature_2m': [merged_data['schedule_relationship_Scheduled'] * merged_data['temperature_2m']]
    }
    
    # Create input matrix
    input_df = pd.DataFrame(input_data)
    return xgb.DMatrix(input_df, enable_categorical=False)
  
if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
