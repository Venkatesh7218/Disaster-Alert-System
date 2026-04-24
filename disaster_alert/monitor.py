import time
import schedule
import json
import os
from datetime import datetime
from dotenv import load_dotenv

from utils.weather_fetcher import get_current_weather, get_forecast_weather
from models.disaster_predictor import predict_disasters, get_overall_risk_level
from alerts.message_generator import generate_alert_message, translate_messages
from alerts.alert_sender import send_all_alerts

load_dotenv()

# How often to check weather (minutes)
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 10))

# Track last alert to avoid spam
last_alert_time = {}
ALERT_COOLDOWN = 30  # minutes between same alert type


def load_alert_log():
    """Load existing alert log"""
    try:
        with open("alert_log.json", "r") as f:
            return json.load(f)
    except:
        return []


def save_alert_log(log):
    """Save alert log"""
    with open("alert_log.json", "w") as f:
        json.dump(log[-500:], f, indent=2)  # keep last 500 entries


def should_send_alert(disaster_type, severity):
    """Check if enough time has passed since last alert of this type"""
    key = f"{disaster_type}_{severity}"
    now = datetime.now()

    if key in last_alert_time:
        elapsed = (now - last_alert_time[key]).seconds / 60
        if elapsed < ALERT_COOLDOWN:
            print(f"[Monitor] Skipping {key} alert - cooldown ({elapsed:.1f}/{ALERT_COOLDOWN} min)")
            return False

    last_alert_time[key] = now
    return True


def run_monitoring_cycle():
    """Single monitoring cycle: fetch → predict → alert"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*50}")
    print(f"[Monitor] Cycle started at {now}")

    # Step 1: Fetch weather
    print("[Monitor] Fetching weather data...")
    weather = get_current_weather()

    if not weather:
        print("[Monitor] Failed to fetch weather. Retrying next cycle.")
        return

    print(f"[Monitor] Weather: {weather['temp']}°C, {weather['weather_desc']}, "
          f"Wind: {weather['wind_speed']}m/s, Rain: {weather['rain_1h']}mm/h")

    # Step 2: Predict disasters
    disasters = predict_disasters(weather)
    overall_risk = get_overall_risk_level(disasters)

    print(f"[Monitor] Risk Level: {overall_risk}")
    if disasters:
        for d in disasters:
            print(f"  → {d['type']} [{d['severity']}]: {d['reason']}")

    log_entry = {
        "timestamp": now,
        "weather": weather,
        "disasters": disasters,
        "risk_level": overall_risk,
        "alerts_sent": []
    }

    # Step 3: Send alerts if needed
    if disasters and overall_risk != "GREEN":
        # Filter to only critical disasters that need alerting
        alert_disasters = [d for d in disasters if should_send_alert(d["type"], d["severity"])]

        if alert_disasters:
            print(f"[Monitor] Generating alert messages for {len(alert_disasters)} disaster(s)...")

            # Generate English messages
            messages_en = generate_alert_message(weather, alert_disasters)

            # Translate to 14 languages
            print("[Monitor] Translating to 14 languages...")
            all_translations = translate_messages(messages_en, alert_disasters)

            # Send alerts
            print("[Monitor] Sending alerts...")
            results = send_all_alerts(all_translations, overall_risk, "English")

            log_entry["alerts_sent"] = {
                "disasters": [d["type"] for d in alert_disasters],
                "messages": messages_en,
                "results": str(results)
            }

            print(f"[Monitor] ✅ Alerts sent successfully!")
        else:
            print("[Monitor] Disasters detected but within cooldown period.")
    else:
        print("[Monitor] ✅ No disasters detected. All clear.")

    # Save log
    alert_log = load_alert_log()
    alert_log.append(log_entry)
    save_alert_log(alert_log)

    print(f"[Monitor] Cycle complete.")
    return log_entry


def start_continuous_monitoring():
    """Start the continuous monitoring loop"""
    print("🚨 DISASTER ALERT SYSTEM STARTING...")
    print(f"📍 Monitoring: {os.getenv('TARGET_CITY', 'Nagpur')}")
    print(f"⏱️  Check interval: every {CHECK_INTERVAL} minutes")
    print("Press Ctrl+C to stop\n")

    # Run immediately on start
    run_monitoring_cycle()

    # Schedule recurring checks
    schedule.every(CHECK_INTERVAL).minutes.do(run_monitoring_cycle)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    start_continuous_monitoring()
