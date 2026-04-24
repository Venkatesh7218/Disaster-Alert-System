import os
import json
import google.generativeai as genai
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

LANGUAGES = {
    "Hindi": "hi",
    "Marathi": "mr",
    "Bengali": "bn",
    "Telugu": "te",
    "Tamil": "ta",
    "Gujarati": "gu",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Punjabi": "pa",
    "Odia": "or",
    "Urdu": "ur",
    "Assamese": "as",
    "Spanish": "es",
    "French": "fr",
}


def generate_alert_message(weather_data, disasters):
    """Use Gemini to generate clear, actionable alert messages"""
    disaster_list = ", ".join([f"{d['type']} ({d['severity']})" for d in disasters])
    reasons = ". ".join([d["reason"] for d in disasters])

    prompt = f"""
You are an emergency alert system. Generate a clear, concise disaster alert message.

Current weather data:
- City: {weather_data.get('city')}
- Temperature: {weather_data.get('temp')}°C (feels like {weather_data.get('feels_like')}°C)
- Humidity: {weather_data.get('humidity')}%
- Wind Speed: {weather_data.get('wind_speed')} m/s
- Rainfall: {weather_data.get('rain_1h')} mm/h
- Conditions: {weather_data.get('weather_desc')}

Detected disasters: {disaster_list}
Reasons: {reasons}

Generate:
1. A SHORT SMS alert (max 160 characters)
2. A DETAILED WhatsApp message (3-4 sentences with safety tips)
3. An IVR voice message (clear, slow speech, 30 seconds max)

Respond in JSON format only with no markdown or backticks:
{{
  "sms": "...",
  "whatsapp": "...",
  "ivr": "..."
}}
"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        messages = json.loads(text)
    except Exception as e:
        print(f"[Gemini] Error: {e}. Using fallback messages.")
        messages = _fallback_messages(weather_data, disasters)

    return messages


def _fallback_messages(weather_data, disasters):
    """Fallback template-based messages if Gemini fails"""
    city = weather_data.get("city", "your area")
    disaster_list = ", ".join([d["type"] for d in disasters])
    severity = disasters[0]["severity"] if disasters else "YELLOW"

    emoji = {"RED": "🔴", "ORANGE": "🟠", "YELLOW": "🟡"}.get(severity, "⚠️")

    tips = {
        "HEATWAVE": "Stay indoors, drink water every 30 mins, avoid sun from 12-4pm.",
        "FLOOD": "Move to higher ground immediately. Avoid floodwater.",
        "STORM": "Stay indoors, avoid trees and electric poles.",
        "CYCLONE": "Evacuate coastal areas immediately. Seek shelter.",
        "DENSE_FOG": "Avoid driving. Use fog lights if necessary.",
        "COLD_WAVE": "Stay warm, wear layers, avoid going out.",
    }

    tip = tips.get(disasters[0]["type"] if disasters else "", "Follow local authority guidelines.")

    return {
        "sms": f"{emoji} ALERT: {disaster_list} in {city}. Temp:{weather_data.get('temp')}°C. {tip[:80]}",
        "whatsapp": f"{emoji} *DISASTER ALERT — {city}*\n\n*Detected:* {disaster_list}\n*Conditions:* {weather_data.get('weather_desc')}, {weather_data.get('temp')}°C\n\n⚠️ *Safety Tips:* {tip}\n\nStay safe and follow local authority instructions.",
        "ivr": f"Emergency alert for {city}. {disaster_list} has been detected. {tip} Please stay safe and follow instructions from local authorities. This message will repeat. {tip}"
    }


def translate_messages(messages, disasters=None):
    """Translate messages into 14 languages using Google Translate (free)"""
    translated = {"English": messages}

    for lang_name, lang_code in LANGUAGES.items():
        try:
            translated[lang_name] = {
                "sms": GoogleTranslator(source="en", target=lang_code).translate(messages["sms"]),
                "whatsapp": GoogleTranslator(source="en", target=lang_code).translate(messages["whatsapp"]),
                "ivr": GoogleTranslator(source="en", target=lang_code).translate(messages["ivr"]),
            }
            print(f"[Translate] ✅ {lang_name}")
        except Exception as e:
            print(f"[Translate] ❌ {lang_name}: {e}")
            translated[lang_name] = messages  # fallback to English

    return translated
