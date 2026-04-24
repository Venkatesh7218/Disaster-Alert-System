import streamlit as st
import json
import os
import time
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.weather_fetcher import get_current_weather
from models.disaster_predictor import predict_disasters, get_overall_risk_level, SEVERITY_COLORS
from alerts.message_generator import generate_alert_message, translate_messages
from alerts.alert_sender import send_all_alerts, load_contacts

load_dotenv()

st.set_page_config(
    page_title="🚨 Disaster Alert System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #FF4B4B; text-align: center;}
    .risk-red {background: #FF4B4B; color: white; padding: 10px; border-radius: 8px; text-align: center; font-size: 1.5rem;}
    .risk-orange {background: #FF8C00; color: white; padding: 10px; border-radius: 8px; text-align: center; font-size: 1.5rem;}
    .risk-yellow {background: #FFD700; color: black; padding: 10px; border-radius: 8px; text-align: center; font-size: 1.5rem;}
    .risk-green {background: #00C853; color: white; padding: 10px; border-radius: 8px; text-align: center; font-size: 1.5rem;}
</style>
""", unsafe_allow_html=True)

CONTACTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contacts.csv")


def load_alert_log():
    try:
        with open("alert_log.json", "r") as f:
            return json.load(f)
    except:
        return []


# ---- SIDEBAR ----
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2620/2620421.png", width=80)
    st.title("⚙️ Controls")

    city = os.getenv("TARGET_CITY", "Nagpur")
    st.info(f"📍 Monitoring: **{city}**")

    st.markdown("---")
    auto_refresh = st.toggle("🔄 Auto Refresh (30s)", value=False)
    manual_check = st.button("🔍 Check Now", use_container_width=True)

    st.markdown("---")

    # ---- CONTACTS UPLOAD ----
    st.markdown("### 👥 Contacts")
    uploaded_csv = st.file_uploader("Upload Contacts CSV", type=["csv"])

    if uploaded_csv:
        df_uploaded = pd.read_csv(uploaded_csv)
        df_uploaded.to_csv(CONTACTS_FILE, index=False)
        st.success(f"✅ {len(df_uploaded)} contacts uploaded!")

    # Show current contacts
    if os.path.exists(CONTACTS_FILE):
        contacts = load_contacts(CONTACTS_FILE)
        st.metric("Total Contacts", len(contacts))
        with st.expander("👁️ View Contacts"):
            df_contacts = pd.read_csv(CONTACTS_FILE)
            st.dataframe(df_contacts, use_container_width=True)
    else:
        st.warning("No contacts file yet. Upload a CSV!")

    st.markdown("---")
    st.markdown("### 📊 Alert Log")
    log = load_alert_log()
    st.metric("Total Cycles", len(log))
    alerts_sent = sum(1 for l in log if l.get("alerts_sent"))
    st.metric("Alerts Sent", alerts_sent)


# ---- MAIN CONTENT ----
st.markdown('<div class="main-header">🚨 Disaster Alert System</div>', unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; color:gray;'>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def fetch_data():
    weather = get_current_weather()
    if weather:
        disasters = predict_disasters(weather)
        risk = get_overall_risk_level(disasters)
        return weather, disasters, risk
    return None, [], "GREEN"


if manual_check:
    st.cache_data.clear()

weather, disasters, risk_level = fetch_data()

if weather:
    risk_class = f"risk-{risk_level.lower()}"
    st.markdown(f'<div class="{risk_class}">{SEVERITY_COLORS.get(risk_level, "🟢 NORMAL")} — Overall Risk Level</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🌡️ Temperature", f"{weather['temp']}°C", f"Feels {weather['feels_like']}°C")
    col2.metric("💧 Humidity", f"{weather['humidity']}%")
    col3.metric("💨 Wind Speed", f"{weather['wind_speed']} m/s")
    col4.metric("🌧️ Rainfall", f"{weather['rain_1h']} mm/h")
    col5.metric("👁️ Visibility", f"{weather['visibility']/1000:.1f} km")

    st.markdown("---")
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("⚠️ Detected Disasters")
        if disasters:
            for d in disasters:
                sev = d["severity"]
                color = {"RED": "🔴", "ORANGE": "🟠", "YELLOW": "🟡"}.get(sev, "🟢")
                with st.expander(f"{color} {d['type']} — {sev}", expanded=(sev == "RED")):
                    st.write(f"**Reason:** {d['reason']}")
                    st.progress(min(d['score'] / 10, 1.0), text=f"Severity Score: {d['score']}/10")
        else:
            st.success("✅ No disasters detected. All clear.")

        if disasters and st.button("🤖 Generate Alert Messages", use_container_width=True):
            with st.spinner("Gemini is generating alert messages..."):
                messages = generate_alert_message(weather, disasters)
                st.session_state["messages"] = messages

        if "messages" in st.session_state:
            msgs = st.session_state["messages"]
            st.subheader("📨 Generated Alert Messages")
            tab1, tab2, tab3 = st.tabs(["📱 SMS", "💬 WhatsApp", "📞 IVR"])
            with tab1:
                st.text_area("SMS", msgs.get("sms", ""), height=80)
            with tab2:
                st.text_area("WhatsApp", msgs.get("whatsapp", ""), height=120)
            with tab3:
                st.text_area("IVR Script", msgs.get("ivr", ""), height=120)

            if st.button("🌍 Translate to 14 Languages", use_container_width=True):
                with st.spinner("Translating via Google Translate..."):
                    translations = translate_messages(msgs, disasters)
                    st.session_state["translations"] = translations
                    st.success("✅ Translated to 14 languages!")

        if "translations" in st.session_state:
            trans = st.session_state["translations"]

            st.subheader("🌍 Preview Translations")
            lang_selected = st.selectbox("Select Language to Preview", list(trans.keys()))
            if lang_selected:
                t = trans[lang_selected]
                st.text_area(f"SMS ({lang_selected})", t.get("sms", ""), height=70)
                st.text_area(f"WhatsApp ({lang_selected})", t.get("whatsapp", ""), height=100)

            st.markdown("---")

            # Show contacts that will receive alerts
            if os.path.exists(CONTACTS_FILE):
                contacts = load_contacts(CONTACTS_FILE)
                st.subheader(f"📋 Will send to {len(contacts)} contacts:")
                for c in contacts:
                    lang_flag = {"Hindi": "🇮🇳", "Marathi": "🇮🇳", "Urdu": "🇵🇰", "French": "🇫🇷",
                                 "Spanish": "🇪🇸", "Bengali": "🇧🇩", "Telugu": "🇮🇳",
                                 "Tamil": "🇮🇳", "Gujarati": "🇮🇳", "English": "🇬🇧"}.get(c["language"], "🌍")
                    st.markdown(f"{lang_flag} **{c['name']}** — {c['phone']} — *{c['language']}*")

            if st.button("📤 Send Alerts to All Contacts", use_container_width=True, type="primary"):
                with st.spinner(f"Sending alerts to all contacts in their language..."):
                    results = send_all_alerts(trans, risk_level, CONTACTS_FILE)
                    st.success(f"✅ Alerts sent to {len(results)} contacts!")
                    with st.expander("View Results"):
                        st.json(results)

    with col_right:
        st.subheader("🗺️ Affected Zone Map")
        lat = weather.get("lat", 21.1458)
        lon = weather.get("lon", 79.0882)

        m = folium.Map(location=[lat, lon], zoom_start=10)
        circle_color = {"RED": "red", "ORANGE": "orange", "YELLOW": "yellow", "GREEN": "green"}.get(risk_level, "green")

        folium.Circle(
            location=[lat, lon], radius=20000,
            color=circle_color, fill=True, fill_opacity=0.3,
            popup=f"Risk: {risk_level}"
        ).add_to(m)

        folium.Marker(
            location=[lat, lon],
            popup=f"{weather['city']} — {risk_level} RISK",
            icon=folium.Icon(color=circle_color if circle_color != "yellow" else "orange",
                             icon="warning-sign", prefix="glyphicon")
        ).add_to(m)

        st_folium(m, height=400, use_container_width=True)

        st.subheader("📋 Recent Alert History")
        log = load_alert_log()
        if log:
            for entry in reversed(log[-5:]):
                ts = entry.get("timestamp", "")
                rl = entry.get("risk_level", "GREEN")
                dis = [d["type"] for d in entry.get("disasters", [])]
                icon = {"RED": "🔴", "ORANGE": "🟠", "YELLOW": "🟡", "GREEN": "🟢"}.get(rl, "🟢")
                st.markdown(f"{icon} `{ts}` — **{rl}** — {', '.join(dis) if dis else 'All Clear'}")
        else:
            st.info("No alert history yet. Run monitor.py to start.")

else:
    st.error("❌ Could not fetch weather data. Check your OpenWeatherMap API key in `.env`")

if auto_refresh:
    time.sleep(30)
    st.rerun()
