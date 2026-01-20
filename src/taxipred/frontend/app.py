import streamlit as st
import httpx 
import folium 
from streamlit_folium import st_folium

# -------- Config ---------
st.set_page_config(page_title="Taxi Price Prediction", page_icon="🚕", layout="wide")

API_BASE = st.sidebar.text_input(
    "API base URL",
    "http://127.0.0.1:8000"
).rstrip("/")

ORS_KEY = st.secrets.get("ORS_API_KEY", "")

# ------- Helpers ----------
def get(path):
    r = httpx.get(f"{API_BASE}{path}", timeout=10)
    r.raise_for_status()
    return r.json()

def post(path, body):
    r = httpx.post(f"{API_BASE}{path}", json=body, timeout=10)
    r.raise_for_status()
    return r.json()

def safe(fn):
    try:
        return fn(), None
    except Exception as e:
        return None, str(e)

# -------- Title -------- 
