import os
import pandas as pd
from twilio.rest import Client
from gtts import gTTS
from dotenv import load_dotenv
import tempfile

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
WHATSAPP_FROM = os.getenv("WHATSAPP_FROM", "whatsapp:+14155238886")

# Initialize Twilio client
try:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    TWILIO_ENABLED = True
except Exception as e:
    print(f"[Twilio] Not configured: {e}")
    TWILIO_ENABLED = False

CONTACTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "contacts.csv")


def load_contacts(csv_path=None):
    """Load contacts from CSV file"""
    path = csv_path or CONTACTS_FILE
    try:
        df = pd.read_csv(path, dtype=str)
        df.columns = [c.strip().lower() for c in df.columns]
        contacts = []
        for _, row in df.iterrows():
            contacts.append({
                "name": str(row.get("name", "")).strip(),
                "phone": str(row.get("phone", "")).strip(),
                "language": str(row.get("language", "English")).strip(),
            })
        print(f"[Contacts] Loaded {len(contacts)} contacts")
        return contacts
    except Exception as e:
        print(f"[Contacts] Error: {e}. Using .env fallback.")
        phones = os.getenv("TARGET_PHONE_NUMBERS", "").split(",")
        return [{"name": "User", "phone": p.strip(), "language": "English"} for p in phones if p.strip()]


def send_sms(message, phone):
    """Send SMS to a single phone"""
    if not TWILIO_ENABLED:
        print(f"[SMS] Simulated → {phone}")
        return {"phone": phone, "status": "simulated"}
    try:
        msg = twilio_client.messages.create(body=message, from_=TWILIO_PHONE_NUMBER, to=phone)
        print(f"[SMS] ✅ Sent to {phone}")
        return {"phone": phone, "status": "sent", "sid": msg.sid}
    except Exception as e:
        print(f"[SMS] ❌ Failed {phone}: {e}")
        return {"phone": phone, "status": "failed", "error": str(e)}


def send_whatsapp(message, phone):
    """Send WhatsApp message to a single phone"""
    if not TWILIO_ENABLED:
        print(f"[WhatsApp] Simulated → {phone}")
        return {"phone": phone, "status": "simulated"}
    try:
        msg = twilio_client.messages.create(body=message, from_=WHATSAPP_FROM, to=f"whatsapp:{phone}")
        print(f"[WhatsApp] ✅ Sent to {phone}")
        return {"phone": phone, "status": "sent", "sid": msg.sid}
    except Exception as e:
        print(f"[WhatsApp] ❌ Failed {phone}: {e}")
        return {"phone": phone, "status": "failed", "error": str(e)}


def send_whatsapp_voice_note(ivr_text, phone, lang="en"):
    """Generate and send voice note via WhatsApp"""
    try:
        tts = gTTS(text=ivr_text, lang=lang, slow=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tts.save(f.name)
        if TWILIO_ENABLED:
            msg = twilio_client.messages.create(
                body=f"🔊 VOICE ALERT: {ivr_text}",
                from_=WHATSAPP_FROM,
                to=f"whatsapp:{phone}"
            )
            print(f"[VoiceNote] ✅ Sent to {phone}")
            return {"phone": phone, "status": "sent", "sid": msg.sid}
        else:
            print(f"[VoiceNote] Simulated → {phone}")
            return {"phone": phone, "status": "simulated"}
    except Exception as e:
        print(f"[VoiceNote] ❌ Failed {phone}: {e}")
        return {"phone": phone, "status": "failed", "error": str(e)}


def make_ivr_call(ivr_message, phone):
    """Make IVR call to a single phone"""
    if not TWILIO_ENABLED:
        print(f"[IVR] Simulated → {phone}")
        return {"phone": phone, "status": "simulated"}
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-IN" rate="slow">{ivr_message}</Say>
    <Pause length="2"/>
    <Say voice="alice" language="en-IN" rate="slow">{ivr_message}</Say>
</Response>"""
    try:
        call = twilio_client.calls.create(twiml=twiml, from_=TWILIO_PHONE_NUMBER, to=phone)
        print(f"[IVR] ✅ Calling {phone}")
        return {"phone": phone, "status": "calling", "sid": call.sid}
    except Exception as e:
        print(f"[IVR] ❌ Failed {phone}: {e}")
        return {"phone": phone, "status": "failed", "error": str(e)}


def send_all_alerts(translations, severity="YELLOW", csv_path=None):
    """
    Send alerts to all contacts in CSV.
    Each contact gets alert in their preferred language.
    """
    contacts = load_contacts(csv_path)
    results = []

    for contact in contacts:
        name = contact["name"]
        phone = contact["phone"]
        language = contact["language"]

        # Get messages in contact's language (fallback to English)
        msg = translations.get(language, translations.get("English", {}))

        print(f"\n[Alert] Sending to {name} ({phone}) in {language}...")

        result = {
            "name": name,
            "phone": phone,
            "language": language,
            "sms": None,
            "whatsapp": None,
            "voice_note": None,
            "ivr": None
        }

        # Send SMS
        result["sms"] = send_sms(msg.get("sms", ""), phone)

        # Send WhatsApp
        result["whatsapp"] = send_whatsapp(msg.get("whatsapp", ""), phone)

        # Send Voice Note
        result["voice_note"] = send_whatsapp_voice_note(msg.get("ivr", ""), phone)

        # IVR call only for RED or ORANGE
        if severity in ["RED", "ORANGE"]:
            result["ivr"] = make_ivr_call(msg.get("ivr", ""), phone)

        results.append(result)

    print(f"\n[Alert] ✅ Alerts sent to {len(results)} contacts!")
    return results
