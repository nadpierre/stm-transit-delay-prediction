from flask import Flask, request, jsonify, render_template
import joblib
import numpy as np

# Import custom code
from src.constants import *
from src.helper_functions import *

app = Flask(__name__)
#model = joblib.load('models/regression_model.pkl')

@app.route('/')
def home():
  return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        feature = float(request.form['feature'])
        # TODO: get other features that are not in form
        prediction = model.predict(np.array([[feature]]))
        return render_template('index.html', prediction=prediction[0])
    except Exception as e:
        return render_template('index.html', prediction=f"Error: {str(e)}")
  
if __name__ == '__main__':
    app.run(debug=True)
