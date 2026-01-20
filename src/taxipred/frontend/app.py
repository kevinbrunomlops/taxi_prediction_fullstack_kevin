import streamlit as st
import httpx 
import pandas as pd 
import json 

st.set_page_config(page_title="Taxi Price Prediction", page_icon="🚕", layout="wide")


ORS_KEY = st.secrets.get("ORS_API_KEY", "")