import streamlit as st
import requests
from geopy.geocoders import Nominatim

SEARCH_RADIUS_METERS = 5000


geolocator = Nominatim(
    user_agent="trail-finder-app",
    timeout=10
)


# -----------------------------
# ZIP → coordinates
# -----------------------------
@st.cache_data
def get_coordinates(zipcode):
    location = geolocator.geocode(
        {"postalcode": zipcode, "country": "USA"}
    )
    if location:
        return location.latitude, location.longitude
    return None, None


# -----------------------------
# Difficulty mapping
# -----------------------------
def get_difficulty(tags):
    sac = tags.get("sac_scale")

    return {
        "hiking": "Easy (Beginner)",
        "mountain_hiking": "Moderate",
        "demanding_mountain_hiking": "Hard",
        "alpine_hiking": "Very Hard",
        "difficult_alpine_hiking": "Extreme"
    }.get(sac, "Unknown")


# -----------------------------
# Reverse geocode city
# -----------------------------

def get_city(lat, lon):
    location = geolocator.reverse((lat, lon), exactly_one=True)
    if location and location.raw.get("address"):
        addr = location.raw["address"]
        return addr.get("city") or addr.get("town") or addr.get("village") or "Unknown"
    return "Unknown"


# -----------------------------
# Overpass API call
# -----------------------------
@st.cache_data(ttl=3600)  # cache for 1 hour
def find_trails(lat, lon):
    query = f"""
    [out:json][timeout:25];
    (
      relation["route"="hiking"](around:{SEARCH_RADIUS_METERS},{lat},{lon});
      way["route"="hiking"](around:{SEARCH_RADIUS_METERS},{lat},{lon});
      way["highway"="path"]["sac_scale"](around:{SEARCH_RADIUS_METERS},{lat},{lon});
    );
    out center tags;
    """

    response = requests.get(
        "https://overpass-api.de/api/interpreter",
        params={"data": query},
        headers={"User-Agent": "trail-finder-app"}
    )

    return response.json()


# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🥾 Trail Finder App")

zipcode = st.text_input("Enter ZIP Code")

if st.button("Find Trails"):

    lat, lon = get_coordinates(zipcode)

    if not lat:
        st.error("Invalid ZIP code")
        st.stop()

    st.success(f"Location: {lat}, {lon}")

    data = find_trails(lat, lon)

    seen = set()
    results = []

    for element in data["elements"]:
        tags = element.get("tags", {})
        name = tags.get("name")

        if not name or name in seen:
            continue

        seen.add(name)

        center = element.get("center")
        if not center:
            continue

        difficulty = get_difficulty(tags)
        #city = get_city(center["lat"], center["lon"])

        results.append({
            "Trail": name,
            "Difficulty": difficulty,
            "Location": f"📍 {center['lat']:.5f}, {center['lon']:.5f}"
        })

    if results:
        st.dataframe(results)
    else:
        st.warning("No trails found nearby")