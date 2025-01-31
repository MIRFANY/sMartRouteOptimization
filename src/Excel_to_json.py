import pandas as pd
import json

# Load the Excel file
file_path = 'Sample Output Trip.xlsx'
sheet_index = 0  # Use the first sheet (index 0)

# Read the specific sheet by index
df = pd.read_excel(file_path, sheet_name=sheet_index)

# Initialize a dictionary to store the trip data
trip_data = {}

# Iterate through the DataFrame
current_trip_id = None
for index, row in df.iterrows():
    if pd.notna(row['TRIP ID']):
        current_trip_id = row['TRIP ID']
        trip_data[current_trip_id] = {
            "Shipments": [],
            "MST_DIST": row['MST_DIST'],
            "TRIP_TIME": row['TRIP_TIME'],
            "Vehical_Type": row['Vehical_Type'],
            "CAPACITY_UTI": row['CAPACITY_UTI'],
            "TIME_UTI": row['TIME_UTI'],
            "COV_UTI": row['COV_UTI']
        }

    if current_trip_id and pd.notna(row['Shipment ID']):
        trip_data[current_trip_id]["Shipments"].append({
            "Shipment ID": row['Shipment ID'],
            "Latitude": row['Latitude'],
            "Longitude": row['Longitude'],
            "TIME SLOT": row['TIME SLOT']
        })

# Convert the dictionary to JSON
json_output = json.dumps(trip_data, indent=4)
# Print the JSON output
print(json_output)

# Optionally, save the JSON to a file
with open('trip_data.json', 'w') as json_file:
    json_file.write(json_output)
