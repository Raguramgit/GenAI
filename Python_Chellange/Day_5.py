# logi_convert.py
"""
Logi Convert — Streamlit micro-SaaS unit converter
Filename: logi_convert.py

Features:
 - Currency (live via exchangerate.host, cached)
 - Temperature (Celsius, Fahrenheit, Delisle, Newton, Kelvin)
 - Length (many units; factors to meter)
 - Power/Electricity (mW, W, kW, MW, GW, hp)
 - Height & Weight converters + BMI with recommendation text
 - Conversion history (session), CSV download, WhatsApp share link
 - Modern styling using provided CSS (Inter font + card layout)
"""

import streamlit as st
import pandas as pd
import requests
import io
import math
import datetime
import time
import urllib.parse
from typing import Dict, Tuple, Any

# Optional: server-side clipboard & local automation
try:
    import pyperclip
except Exception:
    pyperclip = None

# NOTE: Do not import pyautogui here for server safety. We offer a downloadable helper script
# that the user may run locally if they want PyAutoGUI automation.

# ---------------------------
# Page configuration
# ---------------------------
st.set_page_config(page_title="Logi Convert", layout="wide", page_icon="🔁")

# ---------------------------
# Styling (merged user CSS + subtle extras)
# ---------------------------
# Custom CSS for dark theme and modern UI
css = """
<style>
:root{
  --primary-Black: #ffd400;
  --card-bg: rgba(0,0,0,0.35);
  --glass: rgba(255,255,255,0.03);
}
body {
  margin:0;
  font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
}
#root > div:nth-child(1) {
  background: linear-gradient(135deg, #0f2027 0%, #203a43 40%, #2c5364 100%);
}
.stApp {
  background: linear-gradient(-45deg, #ff7b7b, #ffd56b, #7de2ff, #b59bff);
  background-size: 400% 400%;
  animation: gradientBG 9s ease infinite;
}
@keyframes gradientBG {
  0% {background-position: 0% 50%;}
  50% {background-position: 100% 50%;}
  100% {background-position: 0% 50%;}
}
h1, h2, h3, .streamlit-expanderHeader {
  color: var(--primary-Blue) !important;
}
.app-card {
  background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(0,0,0,0.07));
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.25);
  margin-bottom: 14px;
}
.small-muted {
  color: rgba(255,255,255,0.8);
}
.result-bubble {
  background: rgba(255,212,0,0.12);
  padding: 12px;
  border-radius: 10px;
}
.copy-btn {
  background: rgba(0,0,0,0.25);
  color: var(--primary-Red);
  border-radius: 8px;
  padding: 8px 12px;
}
</style>
"""

st.markdown(css, unsafe_allow_html=True)

# ---------------------------
# Helper data & constants
# ---------------------------

CURRENCY_FLAGS = {
    'USD': '🇺🇸', 'INR': '🇮🇳', 'EUR': '🇪🇺', 'GBP': '🇬🇧', 'JPY': '🇯🇵',
    'AUD': '🇦🇺', 'CAD': '🇨🇦', 'CNY': '🇨🇳', 'SGD': '🇸🇬', 'CHF': '🇨🇭',
    'HKD': '🇭🇰', 'NZD': '🇳🇿', 'KRW': '🇰🇷', 'AED': '🇦🇪', 'ZAR': '🇿🇦'
}

CURRENCY_SYMBOL = {
    'USD':'$', 'INR':'₹', 'EUR':'€', 'GBP':'£', 'JPY':'¥', 'AUD':'A$', 'CAD':'C$'
}

# Extend common currency list a bit for convenience
COMMON_CURRENCIES = [
    'USD','EUR','INR','GBP','JPY','AUD','CAD','CNY','SGD','CHF','HKD','NZD','KRW','AED','ZAR'
]

# Length: conversion factors to meters
LENGTH_TO_METER = {
    'millimeter (mm)': 0.001,
    'centimeter (cm)': 0.01,
    'decimeter (dm)': 0.1,
    'meter (m)': 1.0,
    'decameter (dam)': 10.0,
    'hectometer (hm)': 100.0,
    'kilometer (km)': 1000.0,
    'inch (in)': 0.0254,
    'foot (ft)': 0.3048,
    'mile (mi)': 1609.344,
}

# Power -> watts
POWER_TO_WATT = {
    'milliwatt (mW)': 0.001,
    'watt (W)': 1.0,
    'kilowatt (kW)': 1e3,
    'megawatt (MW)': 1e6,
    'gigawatt (GW)': 1e9,
    'horsepower (hp)': 745.699872,
}

# Temperature scales
TEMP_SCALES = ['Celsius (°C)', 'Fahrenheit (°F)', 'Delisle (°De)', 'Newton (°N)', 'Kelvin (K)']

# Height & weight
HEIGHT_UNITS = ['meter (m)', 'centimeter (cm)', 'inch (in)', 'foot (ft)']
WEIGHT_UNITS = ['kilogram (kg)', 'gram (g)', 'pound (lb)', 'ounce (oz)']

# Recommended measuring tools (displayed when toggled)
TOOLS_INFO = {
    'temperature': [
        "Digital thermometer (thermistor)",
        "Infrared thermometer (non-contact)",
        "Thermocouple (industrial)",
        "Resistance Temperature Detector (RTD)",
        "Mercury thermometer (historical/limited use)"
    ],
    'length': [
        "Ruler (mm/cm)",
        "Tape measure (m)",
        "Vernier caliper / digital caliper",
        "Laser distance meter",
        "Measuring wheel"
    ],
    'electricity': [
        "Wattmeter / power meter",
        "Clamp meter (current)",
        "Multimeter (voltage/current/resistance)",
        "Energy meter (kWh meter)"
    ],
    'height_weight': [
        "Measuring tape",
        "Stadiometer (height)",
        "Bathroom scale (home)",
        "Precision balance (clinic)"
    ]
}

# ---------------------------
# Utilities & conversion functions
# ---------------------------

@st.cache_data(ttl=3600)
def fetch_rates(base: str = 'USD') -> Dict[str, float]:
    """
    Fetch exchange rates from exchangerate.host (free) with caching.
    Returns mapping currency -> rate relative to base.
    On failure, returns a conservative fallback mapping (not financial-grade).
    """

    endpoint = f"https://api.exchangerate.host/latest?base={base}"
    try:
        resp = requests.get(endpoint, timeout=6)
        resp.raise_for_status()
        data = resp.json()
        if data and 'rates' in data:
            return data['rates']
    except Exception:
        # swallow network problems and fallback to static approximate rates
        pass

    # Fallback mapping (approximate) — not for trading/financial use
    fallback = {
        'USD':1.0, 'INR':88.26, 'EUR':0.92, 'GBP':0.78, 'JPY':155.0,
        'AUD':1.5, 'CAD':1.35, 'CNY':7.1, 'SGD':1.36, 'CHF':0.91
    }
    # If base present in fallback, normalize accordingly
    if base in fallback:
        base_val = fallback[base]
        return {k: fallback[k] / base_val for k in fallback}
    return fallback

# Temperature (convert via Celsius as intermediary)
def temp_to_celsius(value: float, unit: str) -> float:
    u = unit.lower()
    if 'celsius' in u or '°c' in u:
        return value
    if 'fahren' in u or '°f' in u:
        return (value - 32.0) * 5.0/9.0
    if 'delisle' in u or '°de' in u:
        # C = 100 − D × 2/3
        return 100.0 - (value * 2.0/3.0)
    if 'newton' in u or '°n' in u:
        # C = N × 100/33
        return value * 100.0/33.0
    if 'kelvin' in u or 'k' == u.strip():
        return value - 273.15
    raise ValueError(f"Unsupported temperature unit: {unit}")

def celsius_to_target(c: float, unit: str) -> float:
    u = unit.lower()
    if 'celsius' in u or '°c' in u:
        return c
    if 'fahren' in u or '°f' in u:
        return c * 9.0/5.0 + 32.0
    if 'delisle' in u or '°de' in u:
        # D = (100 − C) × 3/2
        return (100.0 - c) * 3.0/2.0
    if 'newton' in u or '°n' in u:
        return c * 33.0/100.0
    if 'kelvin' in u or 'k' == u.strip():
        return c + 273.15
    raise ValueError(f"Unsupported temperature unit: {unit}")

def convert_temperature(value: float, frm: str, to: str) -> float:
    c = temp_to_celsius(value, frm)
    return celsius_to_target(c, to)

# Length conversions via meters
def convert_length(value: float, frm: str, to: str) -> float:
    if frm not in LENGTH_TO_METER or to not in LENGTH_TO_METER:
        raise ValueError("Unsupported length units.")
    meters = value * LENGTH_TO_METER[frm]
    return meters / LENGTH_TO_METER[to]

# Power conversions via watts
def convert_power(value: float, frm: str, to: str) -> float:
    if frm not in POWER_TO_WATT or to not in POWER_TO_WATT:
        raise ValueError("Unsupported power units.")
    watts = value * POWER_TO_WATT[frm]
    return watts / POWER_TO_WATT[to]

# Height & weight conversions
def convert_height(value: float, frm: str, to: str) -> float:
    # unify to meters
    if 'meter' in frm:
        meters = value
    elif 'centimeter' in frm:
        meters = value / 100.0
    elif 'inch' in frm:
        meters = value * 0.0254
    elif 'foot' in frm:
        meters = value * 0.3048
    else:
        raise ValueError("Unsupported height unit")
    # convert to target
    if 'meter' in to:
        return meters
    if 'centimeter' in to:
        return meters * 100.0
    if 'inch' in to:
        return meters / 0.0254
    if 'foot' in to:
        return meters / 0.3048
    raise ValueError("Unsupported height unit")

def convert_weight(value: float, frm: str, to: str) -> float:
    # unify to kilograms
    if 'kilogram' in frm:
        kg = value
    elif 'gram' in frm:
        kg = value / 1000.0
    elif 'pound' in frm or 'lb' in frm:
        kg = value * 0.45359237
    elif 'ounce' in frm or 'oz' in frm:
        kg = value * 0.028349523125
    else:
        raise ValueError("Unsupported weight unit")
    # to target
    if 'kilogram' in to:
        return kg
    if 'gram' in to:
        return kg * 1000.0
    if 'pound' in to or 'lb' in to:
        return kg / 0.45359237
    if 'ounce' in to or 'oz' in to:
        return kg / 0.028349523125
    raise ValueError("Unsupported weight unit")

# BMI helpers
def calculate_bmi(weight_kg: float, height_m: float) -> float:
    if height_m <= 0 or math.isnan(weight_kg):
        return float('nan')
    return weight_kg / (height_m ** 2)

def bmi_category_and_advice(bmi: float) -> Tuple[str, str]:
    if math.isnan(bmi):
        return 'Unknown', 'Provide valid height and weight.'
    if bmi < 18.5:
        return 'Underweight', 'Increase calorie intake with nutrient-dense foods; add strength training; consider nutrition consult.'
    if bmi < 25.0:
        return 'Normal', 'Maintain balanced diet and regular physical activity — good job!'
    if bmi < 30.0:
        return 'Overweight', 'Aim for modest calorie deficit, increase cardio + strength training; consider professional guidance.'
    return 'Obesity', 'Seek advice from a healthcare professional; consider a structured plan with monitoring.'

# ---------------------------
# Session state: history
# ---------------------------
if 'history' not in st.session_state:
    st.session_state.history = []  # each entry is a dict for CSV export

# Utility: append history safely
def add_history(entry: Dict[str, Any]) -> None:
    st.session_state.history.append(entry)

# ---------------------------
# UI: Header
# ---------------------------
with st.container():
    c1, c2 = st.columns([0.12, 0.88])
    with c1:
        st.markdown("<div class='header'><div style='font-size:175px'>🔁</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("# Logi Convert")
        st.markdown("### A modern micro-SaaS unit converter — Currency, Temperature, Length, Electricity, Height & Weight (+BMI).")
st.divider()

# ---------------------------
# Sidebar options
# ---------------------------
st.sidebar.header("Tools & Options")
conv_type = st.sidebar.selectbox("Converter type",
                                 ["Currency", "Temperature", "Length", "Electricity", "Height & Weight", "BMI"])
show_tools = st.sidebar.checkbox("Show measuring tools", value=True)
use_live_currency = st.sidebar.checkbox("Use live currency rates", value=True)
st.sidebar.markdown("---")
st.sidebar.markdown("**History & quick actions**")
if st.sidebar.button("Clear history"):
    st.session_state.history = []
    st.sidebar.success("History cleared")

# ---------------------------
# Main area: converters
# ---------------------------

# Helper: render share + download UI for a result dict
def render_result_actions(title: str, payload_text: str, csv_df: pd.DataFrame):
    """
    Show share link, copy-to-clipboard (if available), and download CSV for the `csv_df`.
    """
    st.markdown("---")
    st.markdown(f"**{title} — share & export**")
    # WhatsApp share
    wa_url = "https://wa.me/?text=" + urllib.parse.quote_plus(payload_text)
    st.markdown(f"[Share on WhatsApp ▶️]({wa_url})")
    # Copy to clipboard (server)
    if pyperclip:
        if st.button("Copy text to clipboard (server)"):
            try:
                pyperclip.copy(payload_text)
                st.success("Copied to clipboard on the machine running this app.")
            except Exception as e:
                st.error(f"Copy failed: {e}")
    else:
        st.caption("Install `pyperclip` to enable server-side copy to clipboard (optional).")
    # CSV
    csv_bytes = csv_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download result as CSV ⤓", data=csv_bytes, file_name=f"logi_{title.replace(' ','_').lower()}.csv", mime="text/csv")

# ---------------------------
# Currency converter
# ---------------------------
if conv_type == "Currency":
    st.subheader("Currency Converter 💱")
    col_left, col_right = st.columns([1.2, 2.0])
    with col_left:
        amount = st.number_input("Amount", min_value=0.0, value=100.0, format="%.6f")
        from_currency = st.selectbox("From", COMMON_CURRENCIES, index=0)
        to_currency = st.selectbox("To", COMMON_CURRENCIES, index=1)
        convert_btn = st.button("Convert Currency")
    with col_right:
        st.markdown("Live rates are from `exchangerate.host` and are cached for performance. Fallback static rates are used if the API is unavailable.")
        if show_tools:
            st.markdown("**Tools / notes:**")
            st.markdown("- Financial conversions can incur bank spread — for critical payments use your bank or FX provider.")
            st.markdown("- Flag icons shown for common currencies.")

    if convert_btn:
        with st.spinner("Fetching rates and performing conversion..."):
            rates = fetch_rates(base=from_currency) if use_live_currency else fetch_rates(base=from_currency)
            # Unexpected: rates could be empty; guard
            rate = rates.get(to_currency)
            if rate is None:
                st.error("Rate not available for selected pair. Try toggling 'Use live currency rates' or pick another pair.")
            else:
                result = amount * rate
                flag_from = CURRENCY_FLAGS.get(from_currency, "")
                flag_to = CURRENCY_FLAGS.get(to_currency, "")
                symbol = CURRENCY_SYMBOL.get(to_currency, "")
                # Display
                st.markdown(f"## {amount:,.2f} {from_currency} {flag_from} → {symbol} {result:,.2f} {to_currency} {flag_to}")
                st.metric("Exchange rate", f"1 {from_currency} = {rate:.6f} {to_currency}")
                # Nice flavor: show small progress based on magnitude (purely decorative)
                progress_value = min(100, int(min(100, result / max(1.0, amount) * 10)))
                st.progress(progress_value)

                # Save to history
                ts = datetime.datetime.utcnow().isoformat()
                entry = {
                    "timestamp": ts,
                    "category": "Currency",
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "amount": float(amount),
                    "rate": float(rate),
                    "result": float(result)
                }
                add_history(entry)

                # Build CSV & share text
                df = pd.DataFrame([entry])
                share_text = f"Logi Convert — {amount:.2f} {from_currency} = {result:.2f} {to_currency} (rate: {rate:.6f})"
                render_result_actions("Currency", share_text, df)

# ---------------------------
# Temperature converter
# ---------------------------
elif conv_type == "Temperature":
    st.subheader("Temperature Converter 🌡️")
    left, right = st.columns(2)
    with left:
        t_val = st.number_input("Value", value=25.0, format="%.6f")
        t_from = st.selectbox("From", TEMP_SCALES, index=1)
        t_to = st.selectbox("To", TEMP_SCALES, index=0)
        go = st.button("Convert Temperature")
    with right:
        st.markdown("**Scales of temperature**")
        st.markdown("- Celsius (°C), Fahrenheit (°F), Kelvin (K), Delisle (°De) — historical, Newton (°N) — historical.")
        if show_tools:
            st.markdown("**Tools to measure temperature**")
            for t in TOOLS_INFO['temperature']:
                st.write(f"- {t}")

    if go:
        try:
            out = convert_temperature(t_val, t_from, t_to)
            st.metric(f"{t_val} {t_from} →", f"{out:.4f} {t_to}")
            ts = datetime.datetime.utcnow().isoformat()
            entry = {"timestamp": ts, "category": "Temperature", "input_value": float(t_val), "input_unit": t_from, "output_value": float(out), "output_unit": t_to}
            add_history(entry)
            df = pd.DataFrame([entry])
            share_text = f"Temperature: {t_val} {t_from} = {out:.4f} {t_to}"
            render_result_actions("Temperature", share_text, df)
        except Exception as e:
            st.error(f"Conversion failed: {e}")

# ---------------------------
# Length converter
# ---------------------------
elif conv_type == "Length":
    st.subheader("Length Converter 📏")
    a, b = st.columns([1, 2])
    with a:
        val = st.number_input("Value", value=1.0, format="%.6f")
        frm = st.selectbox("From", list(LENGTH_TO_METER.keys()), index=3)
        to = st.selectbox("To", list(LENGTH_TO_METER.keys()), index=9)
        go = st.button("Convert Length")
    with b:
        st.markdown("**Tools to measure length**")
        if show_tools:
            for t in TOOLS_INFO['length']:
                st.write(f"- {t}")

    if go:
        try:
            out = convert_length(val, frm, to)
            st.metric(f"{val} {frm} →", f"{out:.6g} {to}")
            ts = datetime.datetime.utcnow().isoformat()
            entry = {"timestamp": ts, "category": "Length", "input_value": float(val), "input_unit": frm, "output_value": float(out), "output_unit": to}
            add_history(entry)
            df = pd.DataFrame([entry])
            share_text = f"Length: {val} {frm} = {out:.6g} {to}"
            render_result_actions("Length", share_text, df)
        except Exception as e:
            st.error(f"Conversion failed: {e}")

# ---------------------------
# Electricity / Power converter
# ---------------------------
elif conv_type == "Electricity":
    st.subheader("Electricity / Power Converter ⚡")
    l, r = st.columns(2)
    with l:
        val = st.number_input("Value", value=1000.0, format="%.6f")
        frm = st.selectbox("From", list(POWER_TO_WATT.keys()), index=1)
        to = st.selectbox("To", list(POWER_TO_WATT.keys()), index=2)
        go = st.button("Convert Power")
    with r:
        st.markdown("**Tools to measure electrical power**")
        if show_tools:
            for t in TOOLS_INFO['electricity']:
                st.write(f"- {t}")

    if go:
        try:
            out = convert_power(val, frm, to)
            st.metric(f"{val} {frm} →", f"{out:.6g} {to}")
            ts = datetime.datetime.utcnow().isoformat()
            entry = {"timestamp": ts, "category": "Power", "input_value": float(val), "input_unit": frm, "output_value": float(out), "output_unit": to}
            add_history(entry)
            df = pd.DataFrame([entry])
            share_text = f"Power: {val} {frm} = {out:.6g} {to}"
            render_result_actions("Power", share_text, df)
        except Exception as e:
            st.error(f"Conversion failed: {e}")

# ---------------------------
# Height & Weight converter
# ---------------------------
elif conv_type == "Height & Weight":
    st.subheader("Height & Weight Converter 📐⚖️")
    c1, c2 = st.columns(2)
    with c1:
        val_h = st.number_input("Height value", value=170.0, format="%.6f")
        frm_h = st.selectbox("Height unit", HEIGHT_UNITS, index=1)
        to_h = st.selectbox("Convert height to", HEIGHT_UNITS, index=0)
        val_w = st.number_input("Weight value", value=70.0, format="%.6f")
        frm_w = st.selectbox("Weight unit", WEIGHT_UNITS, index=0)
        to_w = st.selectbox("Convert weight to", WEIGHT_UNITS, index=2)
        go = st.button("Convert Height & Weight")
    with c2:
        st.markdown("**Tools for Height & Weight**")
        if show_tools:
            for t in TOOLS_INFO['height_weight']:
                st.write(f"- {t}")

    if go:
        try:
            out_h = convert_height(val_h, frm_h, to_h)
            out_w = convert_weight(val_w, frm_w, to_w)
            st.metric(f"Height: {val_h} {frm_h} →", f"{out_h:.4f} {to_h}")
            st.metric(f"Weight: {val_w} {frm_w} →", f"{out_w:.4f} {to_w}")
            ts = datetime.datetime.utcnow().isoformat()
            entry = {
                "timestamp": ts, "category": "Height & Weight",
                "height_in": f"{val_h} {frm_h}", "height_out": f"{out_h} {to_h}",
                "weight_in": f"{val_w} {frm_w}", "weight_out": f"{out_w} {to_w}"
            }
            add_history(entry)
            df = pd.DataFrame([entry])
            share_text = f"Height: {val_h} {frm_h} = {out_h:.4f} {to_h}; Weight: {val_w} {frm_w} = {out_w:.4f} {to_w}"
            render_result_actions("Height_Weight", share_text, df)
        except Exception as e:
            st.error(f"Conversion failed: {e}")

# ---------------------------
# BMI calculator
# ---------------------------
elif conv_type == "BMI":
    st.subheader("BMI Calculator ⚖️")
    wcol, hcol = st.columns(2)
    with wcol:
        weight_val = st.number_input("Weight", value=70.0, format="%.6f")
        weight_unit = st.selectbox("Weight unit", WEIGHT_UNITS, index=0)
    with hcol:
        height_val = st.number_input("Height", value=170.0, format="%.6f")
        height_unit = st.selectbox("Height unit", HEIGHT_UNITS, index=1)

    if st.button("Calculate BMI"):
        try:
            weight_kg = convert_weight(weight_val, weight_unit, 'kilogram (kg)')
            height_m = convert_height(height_val, height_unit, 'meter (m)')
            bmi = calculate_bmi(weight_kg, height_m)
            cat, advice = bmi_category_and_advice(bmi)
            st.metric(f"BMI: {bmi:.2f} — {cat}", value="")
            st.info(advice)
            ts = datetime.datetime.utcnow().isoformat()
            entry = {"timestamp": ts, "category": "BMI", "weight_kg": float(weight_kg), "height_m": float(height_m), "bmi": float(bmi), "category_label": cat}
            add_history(entry)
            df = pd.DataFrame([entry])
            share_text = f"My BMI: {bmi:.2f} ({cat}). Advice: {advice}"
            render_result_actions("BMI", share_text, df)
        except Exception as e:
            st.error(f"Calculation error: {e}")

# ---------------------------
# Right column / History / Download automation helper
# ---------------------------
st.markdown("---")
st.subheader("Conversion History & Utilities 📜")

if len(st.session_state.history) == 0:
    st.info("You haven't made any conversions yet — try one above.")
else:
    history_df = pd.DataFrame(st.session_state.history)
    # show latest 10
    st.dataframe(history_df.sort_values("timestamp", ascending=False).head(10), use_container_width=True)

    # download full history
    csv_bytes = history_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download full history (CSV) ⤓", data=csv_bytes, file_name="logi_convert_history.csv", mime="text/csv")

    # Offer a textual copy of the last result for quick sharing
    last = st.session_state.history[-1]
    pretty_last = ', '.join([f"{k}: {v}" for k, v in last.items()])
    st.markdown(f"**Latest entry:** {pretty_last}")

# ---------------------------
# Footer: About & instructions
# ---------------------------
st.divider()
with st.container():
    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        st.markdown("**About Logi Convert** — compact unit conversion micro-SaaS demo built with Streamlit.")
    with c2:
        st.markdown("**Quick examples**")
        st.markdown("- `1000 W = 1 kW` (power conversion)\n- `1 USD ≈ 88.26 INR` (example rate)")
    with c3:
        st.markdown("Created by **Raguraman** — Logi Convert")
