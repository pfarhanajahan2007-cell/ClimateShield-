import streamlit as st
import streamlit.components.v1 as components
import requests
from datetime import datetime

st.set_page_config(page_title="ClimateShield Pro", page_icon="🌍", layout="wide")

@st.cache_data(ttl=600)
def locate(city):
    r = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=15,
    )
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return None
    x = results[0]
    return {
        "name": x.get("name", city),
        "country": x.get("country", ""),
        "lat": x["latitude"],
        "lon": x["longitude"],
        "timezone": x.get("timezone", "auto"),
    }

@st.cache_data(ttl=600)
def weather(lat, lon, timezone):
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m",
            "hourly": "precipitation_probability",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "forecast_days": 3,
            "timezone": timezone,
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json()

def description(code):
    return {
        0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",
        45:"Fog",48:"Rime fog",51:"Light drizzle",53:"Moderate drizzle",
        55:"Dense drizzle",61:"Slight rain",63:"Moderate rain",65:"Heavy rain",
        80:"Rain showers",81:"Moderate rain showers",82:"Heavy rain showers",
        95:"Thunderstorm",96:"Thunderstorm with hail",99:"Thunderstorm with heavy hail"
    }.get(code, "Unknown condition")

def risks(current, rain_probability):
    result = []
    temp = current.get("temperature_2m", 0) or 0
    rain = current.get("rain", 0) or 0
    precip = current.get("precipitation", 0) or 0
    wind = current.get("wind_speed_10m", 0) or 0
    code = current.get("weather_code", 0) or 0

    if temp >= 38:
        result.append(("High", "🔥 Heat risk", "Stay hydrated and avoid unnecessary outdoor exposure."))
    elif temp >= 33:
        result.append(("Moderate", "🌡️ Elevated heat", "Drink water and take breaks in cool or shaded areas."))

    if rain >= 10 or precip >= 10 or rain_probability >= 70:
        result.append(("High", "🌧️ Heavy-rain possibility", "Avoid flooded and low-lying areas and check local updates."))
    elif rain > 0 or rain_probability >= 40:
        result.append(("Moderate", "☔ Rain possibility", "Keep rain protection ready and travel carefully."))

    if wind >= 40:
        result.append(("High", "💨 Strong-wind risk", "Avoid loose structures and exposed areas."))
    elif wind >= 25:
        result.append(("Moderate", "🍃 Increased wind", "Be careful near trees and temporary structures."))

    if code in [95, 96, 99]:
        result.append(("High", "⚡ Thunderstorm signal", "Stay indoors during thunder and avoid exposed locations."))

    return result or [("Low", "✅ No major rule-based risk detected", "Continue normal precautions and monitor conditions.")]

st.markdown("# 🌍 ClimateShield Pro")
st.markdown("### Local weather awareness and community safety dashboard")
st.info("Prototype notice: This uses live weather data and simple rules. It is not an official emergency warning system.")

st.sidebar.header("📍 Location")
city = st.sidebar.text_input("Enter your city")
st.sidebar.caption("Workflow: Search → Analyze → Review forecast → Follow safety checklist")

try:
    with st.spinner("Loading live weather data..."):
        loc = locate(city.strip())
        if not loc:
            st.error("Location not found. Try Chennai, Madurai, Coimbatore, or Bengaluru.")
            st.stop()
        data = weather(loc["lat"], loc["lon"], loc["timezone"])

    current = data["current"]
    hourly = data.get("hourly", {})
    daily = data.get("daily", {})
    probabilities = hourly.get("precipitation_probability", [])
    rain_probability = max(probabilities[:6]) if probabilities else 0

    st.success(f"Weather loaded for {loc['name']}, {loc['country']}")
    st.caption(f"Last checked: {datetime.now().strftime('%d %b %Y, %I:%M %p')} | Source: Open-Meteo")

    a,b,c,d = st.columns(4)
    a.metric("🌡️ Temperature", f"{current.get('temperature_2m','—')} °C")
    b.metric("🥵 Feels like", f"{current.get('apparent_temperature','—')} °C")
    c.metric("💨 Wind", f"{current.get('wind_speed_10m','—')} km/h")
    d.metric("🌧️ Rain probability", f"{rain_probability}%")

    st.subheader("🌤️ Current condition")
    st.info(description(current.get("weather_code", 0)))

    st.subheader("🚦 Community risk assessment")
    detected = risks(current, rain_probability)
    x,y,z = st.columns(3)
    x.metric("🔴 High", sum(r[0] == "High" for r in detected))
    y.metric("🟠 Moderate", sum(r[0] == "Moderate" for r in detected))
    z.metric("📌 Total", len(detected))

    for level, title, advice in detected:
        message = f"**{title} — {level}**\n\n{advice}"
        if level == "High":
           st.error(message)

        elif level == "Moderate":
           st.warning(message)

        else:
           st.success(message)

    st.divider()
    st.subheader("📅 3-day forecast")
    dates = daily.get("time", [])
    maxes = daily.get("temperature_2m_max", [])
    mins = daily.get("temperature_2m_min", [])
    rain_probs = daily.get("precipitation_probability_max", [])
    codes = daily.get("weather_code", [])
    cols = st.columns(min(3, len(dates)) or 1)

    for i, date in enumerate(dates[:3]):
        with cols[i]:
            st.markdown(f"**{date}**")
            st.write(description(codes[i]) if i < len(codes) else "—")
            if i < len(maxes) and i < len(mins):
                st.metric("Temperature", f"{maxes[i]} °C", f"Min {mins[i]} °C")
            if i < len(rain_probs):
                st.write(f"🌧️ Rain probability: **{rain_probs[i]}%**")

    st.divider()
    st.subheader("🛡️ Community safety checklist")
    st.checkbox("Check official local weather updates before travelling")
    st.checkbox("Keep drinking water available")
    st.checkbox("Avoid flooded or low-lying areas during heavy rain")
    st.checkbox("Share important alerts with family or neighbours")

    with st.expander("🔎 Technical details"):
        st.json({"coordinates": [loc["lat"], loc["lon"]], "timezone": loc["timezone"], "current": current, "next_6_hours_rain_probability": rain_probability})

except requests.exceptions.RequestException:
    st.error("Could not fetch live weather data. Check your internet connection and try again.")
except Exception as error:
    st.error(f"Unexpected error: {error}")
