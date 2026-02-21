import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

# create your API token, and set it up in Postman collection as part of the Body section
API_TOKEN = ""
# you can get API keys for free here - https://www.visualcrossing.com/weather-api
RSA_KEY = ""

app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


def get_weather(location: str, date: str):
    base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
    unit_group = "metric"
    content_type = "json"

    url = f"{base_url}{location}/{date}?unitGroup={unit_group}&key={RSA_KEY}&contentType={content_type}"

    response = requests.get(url)

    if response.status_code == requests.codes.ok:
        return json.loads(response.text)
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>HW_1 Weather SaaS</h2></p>"


@app.route("/content/api/v1/integration/generate", methods=["POST"])
def weather_endpoint():
    start_dt = dt.datetime.now()
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)

    token = json_data.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    requester_name = json_data.get("requester_name")
    location = json_data.get("location")
    date = json_data.get("date")

    if not requester_name or not location or not date:
        raise InvalidUsage("requester_name, location, and date are required fields", status_code=400)

    weather_data = get_weather(location, date)

    day_data = weather_data["days"][0]

    weather_details = {
        "min_temp_c": day_data.get("tempmin"),
        "max_temp_c": day_data.get("tempmax"),
        "feels_like_c": day_data.get("feelslike"),
        "wind_kph": day_data.get("windspeed"),
        "pressure_mb": day_data.get("pressure"),
        "humidity": day_data.get("humidity")
    }

    result = {
        "requester_name": requester_name,
        "timestamp": dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "location": location,
        "date": date,
        "weather": weather_details
    }

    return result
