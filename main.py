import requests
from geopy.geocoders import Nominatim

SEARCH_RADIUS_METERS = 5000

# -----------------------------
# Convert ZIP code to latitude/longitude
# -----------------------------
def get_coordinates(zipcode):
    geolocator = Nominatim(user_agent="trail_finder")

    location = geolocator.geocode(
        {"postalcode": zipcode, "country": "USA"}
    )

    if location:
        return location.latitude, location.longitude
    else:
        return None, None


# -----------------------------
# Find trails
# -----------------------------
def find_trails(lat, lon):
    query = f"""
    [out:json][timeout:25];
    (
    way["highway"="path"]["sac_scale"](around:{SEARCH_RADIUS_METERS},{lat},{lon});
    way["route"="hiking"](around:{SEARCH_RADIUS_METERS},{lat},{lon});
    relation["route"="hiking"](around:{SEARCH_RADIUS_METERS},{lat},{lon});
    );
    out center tags;
    """

    response = requests.get(
    "https://overpass-api.de/api/interpreter",
    params={"data": query},
    headers={
        "User-Agent": "trail-finder-app"
    }
    
)

   
    data = response.json()
    #print(data)
    seen = set()

    for element in data["elements"]:
        tags = element.get("tags", {})

        name = tags.get("name")
        if not name:
            continue

        if name in seen:
            continue

        seen.add(name)

        sac = tags.get("sac_scale")
        center = element.get("center")
        if sac == "hiking":
            level = "Easy (Beginner)"
        elif sac == "mountain_hiking":
            level = "Moderate"
        elif sac == "demanding_mountain_hiking":
            level = "Hard"
        elif sac == "alpine_hiking":
            level = "Very Hard"
        elif sac == "difficult_alpine_hiking":
            level = "Extreme"
        else:
            level = sac

        print(f"{name} - {level}-{center}")
   

# -----------------------------
# Main
# -----------------------------
zipcode = input("Enter ZIP code: ")

lat, lon = get_coordinates(zipcode)

if lat and lon:
    print(f"Latitude: {lat}")
    print(f"Longitude: {lon}")

    find_trails(lat, lon)
else:
    print("Invalid ZIP code")