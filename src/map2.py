import folium
import Excel_to_json
import requests

# Colors for polyline
colors = ['red', 'blue', 'pink']
# color of polyline

# Set location of the store
store_latitude = 19.075887
store_longitude = 72.877911

# Create a map centered around the store location
m = folium.Map(location=[store_latitude, store_longitude], zoom_start=12)

# Create Marker for the store
store_location = [store_latitude, store_longitude]
folium.Marker(store_location, popup="Intech", icon=folium.Icon(
    color="orange", icon="shopping-cart")).add_to(m)

# Define the route as a list of latitude and longitude points
shipment_points = []
for value in Excel_to_json.trip_data.values():
    trip_id =  value
    vechicle = value['Vehical_Type']
    for coordinates in value["Shipments"]:
        shipment_points.append([coordinates['Latitude'], coordinates['Longitude']])
        folium.Marker(
            [coordinates['Latitude'], coordinates['Longitude']],
            popup=f"Shipment ID: {coordinates['Shipment ID'], trip_id}",
            icon=folium.Icon(color="blue", icon="shopping-cart")
        ).add_to(m)

# Set color
if vechicle == '3W':
    colour_p = colors[0]
if vechicle == '4W-EV':
    colour_p = colors[1]
if vechicle == '4W':
    colour_p = colors[2]

# OpenStreetMap OSRM URL to get routes
url = 'http://router.project-osrm.org/route/v1/driving/'

# Format the URL to add points
url += f"{store_longitude},{store_latitude};"  # Start from the store
for i, cords in enumerate(shipment_points):
    url += f"{cords[1]},{cords[0]}"  # OSRM expects longitude,latitude
    if i < len(shipment_points) - 1:
        url += ";"  # Add semicolon between points, but not at the end
url += f";{store_longitude},{store_latitude}"  # End at the store

# Add the options for the route (e.g., overview=full for full geometry)
url += "?overview=full&geometries=geojson"

# Make the request to the OSRM API
response = requests.get(url)
# Print out the total distance of the trip_id
distance =  response.json()['routes'][0]['distance']
print("total distance of trip = ", distance, "meters")
if response.status_code == 200:
    route_data = response.json()
    # Extract the route geometry (list of coordinates)
    if route_data.get('routes'):
        route_geometry = route_data['routes'][0]['geometry']['coordinates']
        # OSRM gives coordinates in [longitude, latitude], so we need to flip them
        route = [[lat, lon] for lon, lat in route_geometry]
    else:
        route = []
else:
    print("Failed to fetch route data from OSRM API.")
    route = []  # Fallback to an empty list if the API call fails

# Add the route to the map using PolyLine
if route:
    folium.PolyLine(route, color=colour_p, weight=5, opacity=0.7).add_to(m)

    # Add markers for start and end points
    folium.Marker(route[0], popup="Start",
                  icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(route[-1], popup="End",
                  icon=folium.Icon(color="red")).add_to(m)
else:
    print("No route coordinates to display.")

# Save and display the map
m.save("route_map.html")
