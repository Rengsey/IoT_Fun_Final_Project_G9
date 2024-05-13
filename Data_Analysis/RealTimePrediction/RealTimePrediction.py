"""
Real-Time Prediction- Group 4
This script sets up a Flask web server to handle real-time temperature predictions using a pre-trained SVM model.
"""

# Importing necessary libraries
import joblib
import pandas as pd
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS
import json

# Loading the trained SVM model and the column names used for the model input
svm_model1 = joblib.load('svm_model.pkl')  # Load SVM model from file
svm_columns1 = joblib.load("svm_model_columns.pkl")  # Load column names for the model input
svm_model2 = joblib.load('svm_model.pkl')  # Load SVM model from file
svm_columns2 = joblib.load("svm_model_columns.pkl")  # Load column names for the model input
# Load environment variables from a ".env" file for configuration and security

load_dotenv()

# Configuration for InfluxDB: establish connection details using environment variables
BUCKET = os.environ.get('INFLUXDB_BUCKET')
print("Connecting to InfluxDB at URL:", os.environ.get('INFLUXDB_URL'))
client = InfluxDBClient(
    url=str(os.environ.get('INFLUXDB_URL')),
    token=str(os.environ.get('INFLUXDB_TOKEN')),
    org=os.environ.get('INFLUXDB_ORG')
)
write_api = client.write_api()  # Asynchronous write to InfluxDB

# Initialize Flask app for creating a REST API server
app = Flask(__name__)

# A list to store model input
recent_temperatures = []
recent_humidity = []

# Default route to check if the model is loaded properly
@app.route('/')
def check_model():
    if svm_model1&svm_model2:
        return "Model is ready for prediction"
    return "Server is running but something is wrong with the model"

# Route to handle POST requests for predictions
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Extracting JSON data from the POST request
        json_text = request.data
        json_data = json.loads(json_text)

        # Validate presence of expected temperature key in the data
        if 'Temperature' not in json_data:
            return "Invalid input: 'Temperature' key not found in input data.", 400
        
        # Read and append the temperature value to the recent temperatures list
        temp = json_data['Temperature']
        recent_temperatures.append(temp)
        hum = json_data['Humidity']
        recent_humidity.append(hum)
        # Maintain the list at exactly five readings to match the model's input requirements
        if len(recent_temperatures) > 5:
            recent_temperatures.pop(0)
        if len(recent_humidity) > 5:
            recent_humidity.pop(0)
        # Check if enough readings are available to make a prediction
        if len(recent_temperatures) < 5:
            return "Insufficient data: Waiting for five temperature readings before predicting.", 200
        
        # Use recent temperature readings to make a prediction with the SVM model
        query1 = pd.DataFrame([recent_temperatures], columns=svm_columns1)
        predict_sample1 = svm_model1.predict(query1)
        predicted_output1 = float(predict_sample1[0])  # Converting prediction result to float for precision
        query2 = pd.DataFrame([recent_humidity], columns=svm_columns1)
        predict_sample2 = svm_model2.predict(query2)
        predicted_output2 = float(predict_sample2[0])  # Converting prediction result to float for precision
        # Log and write the predicted temperature to InfluxDB
        point = Point("predicted_temperature&humidity")\
            .field("next_temperature", predicted_output1)\
            .field("Error", abs((predicted_output1 - float(temp)) * 100 / float(temp)))\
            .field("next_humidity", predicted_output2)\
            .field("Error", abs((predicted_output2 - float(hum)) * 100 / float(hum)))
        write_api.write(BUCKET, os.environ.get('INFLUXDB_ORG'), point)

        # Return the predicted temperature in JSON format
        return jsonify({"Predicted temperature": predicted_output1}), 200
    
    except Exception as e:
        # Handle errors gracefully and provide feedback
        return f"Error processing the prediction request: {str(e)}", 400
    
# Condition to ensure the script runs only when executed, not when imported
if __name__ == '__main__':
    app.run()  # Start the Flask application
