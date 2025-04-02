import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Firebase Setup
json_file = "firebase-config.json"
if not firebase_admin._apps:
    cred = credentials.Certificate(json_file)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Fetch Data from Firestore
def fetch_data():
    docs = db.collection("satellite_data").order_by("timestamp").stream()
    data_list = [doc.to_dict() for doc in docs]
    return pd.DataFrame(data_list) if data_list else pd.DataFrame()

# Save Data to CSV
def save_to_csv(df):
    csv_filename = "satellite_data.csv"
    df.to_csv(csv_filename, index=False)
    return csv_filename

st.set_page_config(page_title="Surya Narayana Mark-3 Dashboard", layout="wide")
st.title("🛰 Surya Narayana Mark-3: Live Orbital Dashboard")

# Fetch data
df = fetch_data()
if df.empty:
    st.warning("⚠️ No data found in Firestore.")
else:
    csv_file = save_to_csv(df)
    latest_data = df.iloc[-1] if not df.empty else {}
    
    # Set default location to SRM Kattankulathur, Chengalpattu
    lat, lon = 12.8232, 80.0445
    
    # 🌍 **Dark Themed Satellite Map**
    st.subheader("🌍 Live Satellite Position & 3D Orbit")
    col_map, col_3d = st.columns(2)
    
    with col_map:
        satellite_map = folium.Map(location=[lat, lon], zoom_start=6, tiles="OpenStreetMap")
        folium.Marker([lat, lon], popup="🛰 Surya Narayana Mark - 3", icon=folium.Icon(color="blue", icon="info-sign")).add_to(satellite_map)
        folium_static(satellite_map)

    
    with col_3d:
        if "live_location" in df:
            fig_earth = go.Figure(go.Scattergeo(
                lon=[loc.get("longitude", lon) for loc in df["live_location"] if isinstance(loc, dict)],
                lat=[loc.get("latitude", lat) for loc in df["live_location"] if isinstance(loc, dict)],
                mode="lines",
                line=dict(width=2, color="red"),
            ))
            fig_earth.update_geos(projection_type="orthographic")
            st.plotly_chart(fig_earth)
    
    # 📊 Sensor & Orbital Data
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🌡 Temperature Over Time")
        if "temperature" in df:
            fig_temp = px.line(df, x="timestamp", y="temperature", color_discrete_sequence=["#FF5733"], title="Temperature Variation")
            st.plotly_chart(fig_temp)

        st.subheader("🔋 Solar Battery Power")
        if "solar_flux_W_m2" in df:
            fig_solar = px.line(df, x="timestamp", y="solar_flux_W_m2", title="Solar Battery Level", color_discrete_sequence=["#FFD700"])
            st.plotly_chart(fig_solar)
    
    with col2:
        st.subheader("☢ Cosmic Radiation Levels")
        if "cosmic_radiation_uSv_hr" in df:
            fig_radiation = px.line(df, x="timestamp", y="cosmic_radiation_uSv_hr", title="Radiation Levels", color_discrete_sequence=["#FF0000"])
            st.plotly_chart(fig_radiation)
        
        # 🚨 Radiation Alert
        high_radiation = latest_data.get("cosmic_radiation_uSv_hr", 0)
        if high_radiation > 50:
            st.error(f"🚨 High Radiation Alert! Current Level: {high_radiation} μSv/h")
        else:
            st.success(f"✅ Radiation Level Safe: {high_radiation} μSv/h")
    
    # 🚀 Orbital Tracking
    st.subheader("🛰 Orbital Speed & Altitude")
    if "orbital_speed_km_s" in df and "orbital_altitude_km" in df:
        speed = latest_data.get("orbital_speed_km_s", 7.8)
        altitude = latest_data.get("orbital_altitude_km", 400)
        
        col3, col4 = st.columns(2)
        with col3:
            st.metric(label="🚀 Orbital Speed", value=f"{speed} km/s")
        with col4:
            st.metric(label="🛰 Orbital Altitude", value=f"{altitude} km")
    
    # 📋 Live Data Table
    st.subheader("📋 Live Satellite Data Table")
    st.dataframe(df.sort_values(by="timestamp", ascending=False))
    
    # 📥 Download CSV
    st.download_button(label="📥 Download CSV", data=open(csv_file, "rb"), file_name="satellite_data.csv", mime="text/csv")