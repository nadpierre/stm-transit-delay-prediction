from flask import Flask, request, jsonify, render_template
import joblib
import numpy as np
import os

# Import custom code
from src.constants import ROOT_DIR, MODELS_DIR
from src.helper_functions import get_bus_lines, get_bus_directions, get_bus_stops

app = Flask(__name__)
#model = joblib.load('models/regression_model.pkl')
model = None
scaler_path = os.path.join(ROOT_DIR, MODELS_DIR, 'scaler_coords.pkl')
scaler = joblib.load(scaler_path)

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
        feature = float(request.form['feature'])
        # TODO: get other features that are not in form
        prediction = model.predict(np.array([[feature]]))
        return render_template('index.html', prediction=prediction[0])
    except Exception as e:
        return render_template('index.html', error=e)
  
if __name__ == '__main__':
    app.run(debug=True)
