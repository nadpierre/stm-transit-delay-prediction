from flask import Flask, request, jsonify, render_template
import joblib
import numpy as np

# Import custom code
#from src.constants import *
#from src.helper_functions import *

app = Flask(__name__)
#model = joblib.load('models/regression_model.pkl')
model = None
scaler = joblib.load('models/scaler.coords.pkl')

@app.route('/')
def home():
  bus_lines = [48, 49, 69]
  return render_template('index.html', bus_lines=bus_lines)

@app.route('/get-stops', methods=['POST'])
def get_stops():
    stops = []
    bus_line = request.json.get('bus_line')
    direction = request.json.get('direction')
    return jsonify(stops[bus_line][direction])

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
