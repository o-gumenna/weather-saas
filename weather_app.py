import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

# create your API token, and set it up in Postman collection as part of the Body section
API_TOKEN = ""
# you can get API keys for free here - https://www.visualcrossing.com/weather-api
RSA_KEY = ""
# you can get API keys here - https://aistudio.google.com/api-keys
AI_API_KEY = ""

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


# reccomendation for baristas what kind of drink would be suitable to reccomend due to the weather conditions

def get_ai_recommendation(temp_max_c, temp_min_c, wind_kph, feels_like_c, humidity):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={AI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    prompt = f"Today's temperature range is: {temp_max_c}°C - {temp_min_c}°C, feels like temperature: {feels_like_c}°C, wind {wind_kph} km/h, humidity: {humidity}%. Give a short advice (1-2 sentences) on what relevant product a coffee shop should recommend to their customers."

    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == requests.codes.ok:
        response_json = json.loads(response.text)
        return response_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    else:
        return "Couldn't get advice from AI"


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

    ai_advice = get_ai_recommendation(
        day_data.get("tempmax"),
        day_data.get("tempmin"),
        day_data.get("windspeed"),
        day_data.get("feelslike"),
        day_data.get("humidity")
    )

    result = {
        "requester_name": requester_name,
        "timestamp": dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "location": location,
        "date": date,
        "weather": weather_details,
        "ai_recommendation": ai_advice
    }

    return result
