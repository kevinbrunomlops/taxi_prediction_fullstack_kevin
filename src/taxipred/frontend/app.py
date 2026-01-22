import streamlit as st
import httpx
import folium
from streamlit_folium import st_folium
import polyline

if "route_latlon" not in st.session_state:
    st.session_state.route_latlon = None
if "route_summary" not in st.session_state:
    st.session_state.route_summary = None
if "route_A" not in st.session_state:
    st.session_state.route_A = None
if "route_B" not in st.session_state:
    st.session_state.route_B = None


# -------- Config ---------
st.set_page_config(page_title="Taxi Price Prediction", page_icon="🚕", layout="wide")

ORS_KEY = st.secrets.get("ORS_API_KEY", "")
API_BASE = st.sidebar.text_input("API base URL", "http://127.0.0.1:8000").rstrip("/")




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

# -------- Health ---------
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
            st.success(f"Predicted price: {result['prediction']:.2f}$")


# =====================
#        ROUTE
# =====================
with tab_route:
    st.subheader("Choose destination")

    A = st.text_input("Point A", "From")
    B = st.text_input("Point B", "To")

    rc1, rc2 = st.columns(2)
    with rc1:
        route_passengers = st.number_input(
            "Passenger_Count (route)", min_value=0, value=1, key="route_passengers"
        )
    with rc2:
        route_tod = st.selectbox(
            "Time_of_Day (route) ",
            ["Morning", "Afternoon", "Evening", "Night"],
            key="route_tod"
        )

    if not ORS_KEY:
        st.info("Set ORS_API_KEy to show route on map")
        st.code('export ORS_API_Key="DIN_NYCKEL_HAR')
        st.stop()

    def geocode(q: str):
        r = httpx.get(
            "https://api.openrouteservice.org/geocode/search",
            params={"api_key": ORS_KEY, "text": q, "size": 1, "boundary.country": "SE"},
            timeout=15,
        )
        r.raise_for_status()
        js = r.json()
        feats = js.get("features", [])
        if not feats:
            raise ValueError(f"No match for: {q}")
        lon, lat = feats[0]["geometry"]["coordinates"]
        label = feats[0]["properties"].get("label", q)
        return lat, lon, label

    def route(a, b):
        r = httpx.post(
            "https://api.openrouteservice.org/v2/directions/driving-car",
            headers={"Authorization": ORS_KEY, "Content-Type": "application/json"},
            json={"coordinates": [[a[1], a[0]], [b[1], b[0]]]},
            timeout=20,
        )
        r.raise_for_status()
        js = r.json()

        if "routes" not in js or not js["routes"]:
            raise ValueError(f"ORS directions error: {js}")
        
        summary = js["routes"][0]["summary"]
        encoded = js["routes"][0]["geometry"]
        latlon = polyline.decode(encoded)

        return latlon, summary

    if st.button("SHOW ROUTE", type="primary"):
        A_geo, errA = safe(lambda: geocode(A))
        B_geo, errB = safe(lambda: geocode(B))

        if errA:
            st.warning(f"Could not find point A: {errA}")
        elif errB:
            st.warning(f"Could not find point B: {errB}")
        else:
            res, errR = safe(lambda: route(A_geo, B_geo))
            if errR:
                st.warning(f"Could not fetch route:{errR}")
            else:
                latlon, summary = res
                st.session_state.route_latlon = latlon
                st.session_state.route_summary = summary
                st.session_state.route_A = A_geo
                st.session_state.route_B = B_geo
    
    if st.session_state.route_latlon:
        latlon = st.session_state.route_latlon
        summary= st.session_state.route_summary
        A_geo = st.session_state.route_A
        B_geo = st.session_state.route_B

        st.success(f"Distance: {summary['distance']/1000:.2f} km • Time: {summary['duration']/60:.0f} min")

        distance_km = summary["distance"] / 1000
        duration_min = summary["duration"] / 60

        payload = {
            "Trip_Distance_km": float(distance_km),
            "Trip_Duration_Minutes": float(duration_min),
            "Time_of_Day": st.session_state.get("route_tod", "Morning"),
            "Passenger_Count": int(st.session_state.get("route_passengers", 1)),
        }

        pred_res, pred_err = safe(lambda:post("/predict", payload))
        if pred_err:
            st.warning(f"Price prediction failed: {pred_err}")
        else:
            st.metric("Predicted price for this route", f"{pred_res['prediction']:.2f}$")

        m = folium.Map(location=latlon[0], zoom_start=11)
        folium.Marker(A_geo[:2], tooltip="A",  popup=A_geo[2]).add_to(m)
        folium.Marker(B_geo[:2], tooltip="B", popup=B_geo[2]).add_to(m)
        folium.PolyLine(latlon).add_to(m)
        st_folium(m, height=520, use_container_width=True)

        if st.button("Clear route"):
            st.session_state.route_latlon = None
            st.session_state.route_summary = None
            st.session_state.route_A = None
            st.session_state.route_B = None
                
