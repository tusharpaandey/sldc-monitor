import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
from datetime import datetime

# --- Configuration ---
st.set_page_config(page_title="BSES Control Room (Demo)", layout="wide", page_icon="⚡")

# Dashboard Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1c2128; border-radius: 8px; padding: 15px; border: 1px solid #30363d; margin-bottom: 10px;}
    .clock-text { font-size: 24px; font-family: 'Courier New', Courier, monospace; color: #00ff00; font-weight: bold; text-align: right; }
    .tutorial-box { background-color: #1a1a2e; padding: 20px; border-radius: 8px; border-left: 5px solid #ff0000; margin-bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

# --- Image Helper ---
def get_logo_path():
    """Checks for both png and jpg extensions."""
    if os.path.exists("logo.png"): return "logo.png"
    if os.path.exists("logo.jpg"): return "logo.jpg"
    return None

logo_path = get_logo_path()

# --- 1. Login Gate (REWRITTEN WITHOUT COLUMNS) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Using a simple container instead of columns
    st.write("") # Spacer
    st.write("") # Spacer
    
    if logo_path:
        st.image(logo_path, width=300) # Hardcoded width instead of column width
        
    st.title("⚡ Control Room Login")
    st.info("👋 **Welcome to the Interactive Demo!** \n\nLog in using Username: `1` and Password: `1`")
    
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    
    if st.button("Access Dashboard") or (u == "1" and p == "1"):
        if u == "1" and p == "1":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid credentials. Use 1 and 1.")
    st.stop()

# --- 2. Synthetic Data Engine ---
def generate_dummy_data(revision):
    """Generates synthetic 96-block power schedule data for the demo."""
    np.random.seed(revision) 
    periods = list(range(1, 97))
    
    dadri_thermal = np.full(96, 450.0) + np.random.normal(0, 5, 96)
    aravali_power = np.full(96, 200.0) + np.random.normal(0, 3, 96)
    solar_seci = np.clip(np.sin(np.linspace(-0.5, 3.5, 96)) * 120 + np.random.normal(0, 2, 96), 0, None)
    wind_energy = np.random.uniform(30, 80, 96)
    
    df = pd.DataFrame({
        'Period': periods,
        'Dadri_Thermal_MW': np.round(dadri_thermal, 2),
        'Aravali_Power_MW': np.round(aravali_power, 2),
        'SECI_Solar_MW': np.round(solar_seci, 2),
        'Wind_Farms_MW': np.round(wind_energy, 2)
    })
    return df

# Initialize Session State Variables
if 'rev' not in st.session_state:
    st.session_state.rev = 1
if 'last_rev_audio' not in st.session_state:
    st.session_state.last_rev_audio = 0

df = generate_dummy_data(st.session_state.rev)

# --- 3. Header & Branding ---
# Switched to simple integer specification to avoid list errors
h1, h2, h3 = st.columns(3)
with h1:
    if logo_path:
        st.image(logo_path, width=150)
    else:
        st.warning("⚠️ logo image not found in the Demo folder.")
with h2:
    st.title("Intraday Load Monitor")
with h3:
    st.markdown(f'<p class="clock-text">🕒 {datetime.now().strftime("%H:%M:%S")}</p>', unsafe_allow_html=True)

# --- 4. Main Layout (Tabs for Interactivity) ---
tab_dashboard, tab_tutorial = st.tabs(["🎛️ Live Dashboard", "📖 How to Use This Tool"])

with tab_tutorial:
    st.markdown("""
    <div class="tutorial-box">
        <h3>Welcome to the BSES Control Room Demo!</h3>
        <p>This tool is designed to help operators manage power schedules efficiently. Here is how to test the features:</p>
        <ol>
            <li><strong>Simulate a Grid Update:</strong> Go to the <b>Live Dashboard</b> tab and click the red "Simulate SLDC Revision" button.</li>
            <li><strong>Audio Alerts:</strong> It plays the chime if there is a schedule change in a revision.</li>
            <li><strong>Analyze Trends:</strong> Select different power plants from the dropdown to see their generation curve over the 96 blocks (15-minute intervals).</li>
            <li><strong>Export Data:</strong> Click the download button to save the current grid state as a CSV file to your local machine.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

with tab_dashboard:
    st.markdown("### 🎛️ Grid Controls")
    
    if st.button("🚨 Simulate SLDC Revision", type="primary", help="Click this to generate a new 96-block schedule."):
        st.session_state.rev += 1
        df = generate_dummy_data(st.session_state.rev)

    # Revision Audio Alert
    if st.session_state.rev > st.session_state.last_rev_audio:
        if os.path.exists("Chime.mp3"):
            with open("Chime.mp3", "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode()
                audio_html = f"""
                    <audio autoplay>
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                    </audio>
                    """
                st.markdown(audio_html, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Chime.mp3 not found in the Demo folder.")
            
        st.session_state.last_rev_audio = st.session_state.rev
        st.toast(f"New Revision Received: Rev {st.session_state.rev}", icon="🔔")

    # Metrics Row
    m1, m2, m3 = st.columns(3)
    m1.metric("Current Revision", f"REV {st.session_state.rev}", delta="+1" if st.session_state.rev > 1 else None)
    m2.metric("System Total Load", f"{round(df.drop('Period', axis=1).sum().sum() / 96, 2)} MW")
    m3.metric("API Status", "🟢 CONNECTED (SIMULATED)")

    st.divider()

    # Plant Selector Detail View
    st.subheader("🔍 Individual Plant Schedule")
    plant_cols = [c for c in df.columns if c != 'Period']
    selected_plant = st.selectbox("Select Plant to Inspect", sorted(plant_cols))

    d1, d2 = st.columns(2)
    with d1:
        st.write(f"**Selected:** {selected_plant.replace('_', ' ')}")
        st.write(f"**Total Scheduled Energy:** {round(df[selected_plant].sum() / 4, 2)} MWh") 
        
        # Export to CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Current Revision", data=csv, file_name=f"BSES_Schedule_Rev_{st.session_state.rev}.csv", mime='text/csv')

    with d2:
        st.line_chart(df.set_index('Period')[selected_plant], height=250, use_container_width=True)

    st.divider()

    # Bottom Consolidated View
    st.subheader("📊 Consolidated View (All Grid Inputs)")
    st.dataframe(df, height=350, use_container_width=True)
