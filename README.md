# 🚨 Disaster Alert System

An AI-powered real-time disaster prediction and multi-channel alert system.

## 📁 Project Structure
```
disaster_alert/
├── .env                        # API keys (fill this first!)
├── requirements.txt            # Dependencies
├── monitor.py                  # Continuous background monitor
├── dashboard.py                # Streamlit web dashboard
├── alert_log.json              # Auto-generated alert history
├── utils/
│   └── weather_fetcher.py      # OpenWeatherMap API
├── models/
│   └── disaster_predictor.py   # Disaster prediction logic
└── alerts/
    ├── message_generator.py    # Claude AI message + translation
    └── alert_sender.py         # Twilio SMS / WhatsApp / IVR
```

## 🚀 Quick Start

### Step 1 — Fill in your API keys
Edit the `.env` file and add your keys:
- OpenWeatherMap: https://openweathermap.org/api
- Anthropic Claude: https://console.anthropic.com
- Twilio: https://twilio.com

### Step 2 — Run the Dashboard
```bash
cd disaster_alert
py -3.11 -m streamlit run dashboard.py
```

### Step 3 — Run the Background Monitor
Open a second terminal:
```bash
cd disaster_alert
py -3.11 monitor.py
```

## 🌍 Features
- ✅ Real-time weather monitoring (every 10 min)
- ✅ AI prediction: Flood, Heatwave, Storm, Cyclone, Fog, Cold Wave
- ✅ Claude AI generates alert messages
- ✅ Translations in 14 languages
- ✅ SMS via Twilio
- ✅ WhatsApp messages + voice notes
- ✅ IVR automated calls (RED/ORANGE alerts only)
- ✅ Live map with risk zones
- ✅ Alert history log

## 🔧 Configuration
Edit `.env` to change:
- `TARGET_CITY` — city to monitor
- `TARGET_LAT` / `TARGET_LON` — coordinates
- `CHECK_INTERVAL` — minutes between checks
- `TARGET_PHONE_NUMBERS` — comma-separated numbers to alert

## 📱 Alert Channels by Severity
| Severity | SMS | WhatsApp | IVR Call |
|----------|-----|----------|----------|
| 🔴 RED   | ✅  | ✅       | ✅       |
| 🟠 ORANGE| ✅  | ✅       | ✅       |
| 🟡 YELLOW| ✅  | ✅       | ❌       |
