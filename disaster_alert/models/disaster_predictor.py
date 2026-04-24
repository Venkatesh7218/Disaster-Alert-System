import numpy as np

# Thresholds for disaster prediction
THRESHOLDS = {
    "flood": {
        "rain_1h": 50,        # mm/h - heavy rain
        "humidity": 90,        # %
        "wind_speed": 15,      # m/s
    },
    "heatwave": {
        "temp": 42,            # °C
        "feels_like": 45,      # °C
        "humidity": 30,        # %
    },
    "storm": {
        "wind_speed": 20,      # m/s
        "rain_1h": 30,         # mm/h
    },
    "cyclone": {
        "wind_speed": 33,      # m/s (hurricane force)
        "pressure": 980,       # hPa (low pressure)
    },
    "dense_fog": {
        "visibility": 200,     # meters
        "humidity": 95,        # %
    },
    "cold_wave": {
        "temp": 5,             # °C
        "feels_like": 2,       # °C
    },
    "drought_risk": {
        "humidity": 15,        # %
        "temp": 40,            # °C
        "rain_1h": 0,          # no rain
    }
}

SEVERITY_COLORS = {
    "RED": "🔴 CRITICAL",
    "ORANGE": "🟠 HIGH",
    "YELLOW": "🟡 MODERATE",
    "GREEN": "🟢 NORMAL"
}


def predict_disasters(weather_data):
    """
    Predict disasters based on current weather data.
    Returns list of detected disasters with severity.
    """
    if not weather_data:
        return []

    disasters = []

    temp = weather_data.get("temp", 0)
    feels_like = weather_data.get("feels_like", 0)
    humidity = weather_data.get("humidity", 0)
    pressure = weather_data.get("pressure", 1013)
    wind_speed = weather_data.get("wind_speed", 0)
    rain_1h = weather_data.get("rain_1h", 0)
    visibility = weather_data.get("visibility", 10000)
    weather_main = weather_data.get("weather_main", "").lower()

    # --- FLOOD ---
    flood_score = 0
    if rain_1h >= THRESHOLDS["flood"]["rain_1h"]:
        flood_score += 3
    elif rain_1h >= 20:
        flood_score += 2
    elif rain_1h >= 10:
        flood_score += 1
    if humidity >= THRESHOLDS["flood"]["humidity"]:
        flood_score += 1
    if wind_speed >= THRESHOLDS["flood"]["wind_speed"]:
        flood_score += 1
    if "rain" in weather_main or "thunderstorm" in weather_main:
        flood_score += 1

    if flood_score >= 4:
        disasters.append({"type": "FLOOD", "severity": "RED", "score": flood_score,
                          "reason": f"Heavy rainfall {rain_1h}mm/h, humidity {humidity}%"})
    elif flood_score >= 2:
        disasters.append({"type": "FLOOD", "severity": "ORANGE", "score": flood_score,
                          "reason": f"Moderate rainfall {rain_1h}mm/h, humidity {humidity}%"})
    elif flood_score >= 1:
        disasters.append({"type": "FLOOD", "severity": "YELLOW", "score": flood_score,
                          "reason": f"Light rainfall {rain_1h}mm/h, monitor situation"})

    # --- HEATWAVE ---
    heat_score = 0
    if temp >= THRESHOLDS["heatwave"]["temp"]:
        heat_score += 3
    elif temp >= 38:
        heat_score += 2
    elif temp >= 35:
        heat_score += 1
    if feels_like >= THRESHOLDS["heatwave"]["feels_like"]:
        heat_score += 2
    elif feels_like >= 40:
        heat_score += 1

    if heat_score >= 4:
        disasters.append({"type": "HEATWAVE", "severity": "RED", "score": heat_score,
                          "reason": f"Extreme temperature {temp}°C, feels like {feels_like}°C"})
    elif heat_score >= 2:
        disasters.append({"type": "HEATWAVE", "severity": "ORANGE", "score": heat_score,
                          "reason": f"High temperature {temp}°C, feels like {feels_like}°C"})
    elif heat_score >= 1:
        disasters.append({"type": "HEATWAVE", "severity": "YELLOW", "score": heat_score,
                          "reason": f"Elevated temperature {temp}°C"})

    # --- STORM ---
    storm_score = 0
    if wind_speed >= THRESHOLDS["storm"]["wind_speed"]:
        storm_score += 3
    elif wind_speed >= 15:
        storm_score += 2
    elif wind_speed >= 10:
        storm_score += 1
    if rain_1h >= THRESHOLDS["storm"]["rain_1h"]:
        storm_score += 2
    if "thunderstorm" in weather_main:
        storm_score += 2

    if storm_score >= 4:
        disasters.append({"type": "STORM", "severity": "RED", "score": storm_score,
                          "reason": f"Wind speed {wind_speed}m/s with heavy rain"})
    elif storm_score >= 2:
        disasters.append({"type": "STORM", "severity": "ORANGE", "score": storm_score,
                          "reason": f"Wind speed {wind_speed}m/s"})

    # --- CYCLONE ---
    if wind_speed >= THRESHOLDS["cyclone"]["wind_speed"] and pressure <= THRESHOLDS["cyclone"]["pressure"]:
        disasters.append({"type": "CYCLONE", "severity": "RED", "score": 10,
                          "reason": f"Cyclonic conditions: wind {wind_speed}m/s, pressure {pressure}hPa"})
    elif wind_speed >= 25 and pressure <= 990:
        disasters.append({"type": "CYCLONE", "severity": "ORANGE", "score": 7,
                          "reason": f"Possible cyclone development: wind {wind_speed}m/s"})

    # --- DENSE FOG ---
    if visibility <= THRESHOLDS["dense_fog"]["visibility"] and humidity >= THRESHOLDS["dense_fog"]["humidity"]:
        disasters.append({"type": "DENSE_FOG", "severity": "ORANGE", "score": 5,
                          "reason": f"Visibility {visibility}m, humidity {humidity}%"})
    elif visibility <= 500:
        disasters.append({"type": "DENSE_FOG", "severity": "YELLOW", "score": 3,
                          "reason": f"Low visibility {visibility}m"})

    # --- COLD WAVE ---
    if temp <= THRESHOLDS["cold_wave"]["temp"] and feels_like <= THRESHOLDS["cold_wave"]["feels_like"]:
        disasters.append({"type": "COLD_WAVE", "severity": "RED", "score": 6,
                          "reason": f"Dangerously cold: {temp}°C, feels like {feels_like}°C"})
    elif temp <= 8:
        disasters.append({"type": "COLD_WAVE", "severity": "ORANGE", "score": 4,
                          "reason": f"Very cold temperature: {temp}°C"})

    # Sort by severity (RED > ORANGE > YELLOW)
    severity_order = {"RED": 0, "ORANGE": 1, "YELLOW": 2, "GREEN": 3}
    disasters.sort(key=lambda x: severity_order.get(x["severity"], 3))

    return disasters


def get_overall_risk_level(disasters):
    """Get overall risk level from list of disasters"""
    if not disasters:
        return "GREEN"
    severities = [d["severity"] for d in disasters]
    if "RED" in severities:
        return "RED"
    elif "ORANGE" in severities:
        return "ORANGE"
    elif "YELLOW" in severities:
        return "YELLOW"
    return "GREEN"
