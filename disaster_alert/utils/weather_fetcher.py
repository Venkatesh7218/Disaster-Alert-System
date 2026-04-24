import requests
import os
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
TARGET_CITY = os.getenv("TARGET_CITY", "Nagpur")
TARGET_LAT = float(os.getenv("TARGET_LAT", 21.1458))
TARGET_LON = float(os.getenv("TARGET_LON", 79.0882))


def get_current_weather():
    """Fetch current weather data from OpenWeatherMap"""
    url = f"https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": TARGET_LAT,
        "lon": TARGET_LON,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return {
            "city": data.get("name", TARGET_CITY),
            "temp": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"]["speed"],
            "wind_deg": data["wind"].get("deg", 0),
            "weather_main": data["weather"][0]["main"],
            "weather_desc": data["weather"][0]["description"],
            "visibility": data.get("visibility", 10000),
            "clouds": data["clouds"]["all"],
            "rain_1h": data.get("rain", {}).get("1h", 0),
            "lat": TARGET_LAT,
            "lon": TARGET_LON,
        }
    except Exception as e:
        print(f"[Weather] Error fetching weather: {e}")
        return None


def get_forecast_weather():
    """Fetch 5-day forecast from OpenWeatherMap"""
    url = f"https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": TARGET_LAT,
        "lon": TARGET_LON,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "cnt": 16  # next 48 hours (3h intervals)
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        forecasts = []
        for item in data["list"]:
            forecasts.append({
                "time": item["dt_txt"],
                "temp": item["main"]["temp"],
                "humidity": item["main"]["humidity"],
                "wind_speed": item["wind"]["speed"],
                "rain": item.get("rain", {}).get("3h", 0),
                "weather_main": item["weather"][0]["main"],
            })
        return forecasts
    except Exception as e:
        print(f"[Weather] Error fetching forecast: {e}")
        return []
