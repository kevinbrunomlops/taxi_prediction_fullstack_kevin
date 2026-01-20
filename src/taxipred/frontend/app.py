import streamlit as st
import httpx
import folium
from streamlit_folium import st_folium
import os

# -------- Config ---------
st.set_page_config(page_title="Taxi Price Prediction", page_icon="🚕", layout="wide")

API_BASE = st.sidebar.text_input("API base URL", "http://127.0.0.1:8000").rstrip("/")

ORS_KEY = os.getenv("ORS_API_KEY", "")


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
st.title("Taxi Price App 🚕")
st.caption("Minimal Streamlit-frontend that consumes FastAPI")

# -------- Halth ---------
health, err = safe(lambda: get("/health"))
if err:
    st.error(f"Could not connect with API: {err}")
    st.stop()

st.success("API succesfully connected")
st.caption(f"Number of rows in dataset: {health.get('rows', '?')}")


tab_predict, tab_route = st.tabs(["Predict 🔮", "Route 🗺️"])

# ====================
#       PREDICT
# ====================
with tab_predict:
    st.subheader("Price prediction")

    (
        c1,
        c2,
        c3,
        c4,
    ) = st.columns(4)

    with c1:
        distance = st.number_input("Trip_Distance_km", 0.0, value=5.0)
    with c2:
        duration = st.number_input("Trip_Duration_Minutes", 0.0, value=15.0)
    with c3:
        passengers = st.number_input("Passenger_Count", 0, value=1)
    with c4:
        tod = st.selectbox("Time_of_Day", ["Morning", "Afternoon", "Evening", "Night"])

    if st.button("PREDICT", type="primary"):
        payload = {
            "Trip_Distance_km": distance,
            "Trip_Duration_Minutes": duration,
            "Time_of_Day": tod,
            "Passenger_Count": passengers,
        }

        result, err = safe(lambda: post("/predict", payload))
        if err:
            st.warning(f"Prediction failed: {err}")
        else:
            st.success(f"Predicted price: {result['prediction']:.2f}")


# =====================
#        ROUTE
# =====================
with tab_route:
    st.subheader("Point A -> Point B")

    if not ORS_KEY:
        st.info("Set ORS_API_KEy to show route on map")
        st.stop()

    A = st.text_input("Point A", "Stockholm Centralstation")
    B = st.text_input("Point B", "Arlanda Airport")

    def geocode(q):
        r = httpx.get(
            "https://api.openrouteservice.org/geocode/search",
            params={"api_key": ORS_KEY, "text": q, "size": 1},
            timeout=15,
        )
        r.raise_for_status()
        f = r.json()["features"][0]
        lon, lat = f["geometry"]["coordinates"]
        return lat, lon, f["properties"]["label"]

    def route(a, b):
        r = httpx.post(
            "https://api.openrouteservice.org/v2/directions/driving-car",
            headers={"Authorization": ORS_KEY},
            json={"coordinates": [[a[1], a[0], b[1], b[0]]]},
            timeout=20,
        )
        r.raise_for_status()
        coords = r.json()["features"][0]["geometry"]["coordinates"]
        return [(c[1], c[0]) for c in coords]

    if st.button("SHOW ROUTE", type="primary"):
        A_geo, errA = safe(lambda: geocode(A))
        B_geo, errB = safe(lambda: geocode(B))

        if errA or errB:
            st.warning("Could not find any of the places.")
            st.stop()

        path, errR = safe(lambda: route(A_geo, B_geo))
        if errR:
            st.warning(f"Could not catch route: {errR}")
            st.stop()

        m = folium.Map(location=path[0], zoom_start=11)
        folium.Marker(A_geo[:2], tooltip="A").add_to(m)
        folium.Marker(B_geo[:2], tooltip="B").add_to(m)
        folium.PolyLine(path).add_to(m)

        st_folium(m, height=500, use_container_width=True)

st.caption("Swagger UI: /docs")
