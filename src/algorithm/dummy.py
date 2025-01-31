import os
import pandas as pd

# Creating sample data for Shipments_Data
shipments_data = pd.DataFrame({
    "Shipment ID": range(1, 10),  # More than 3 samples
    "Latitude": [19.080268, 19.112110, 19.058145, 19.176505, 19.148967, 19.134598, 19.098765, 19.167890, 19.090123],
    "Longitude": [72.850804, 72.898355, 72.834377, 72.962189, 72.931665, 72.876543, 72.912345, 72.845678, 72.867890],
    "Delivery Timeslot": ["09:30:00-12:00:00", "09:30:00-12:00:00", "07:00:00-09:30:00",
                           "12:00:00-14:30:00", "09:30:00-12:00:00", "14:30:00-17:00:00",
                           "07:00:00-09:30:00", "12:00:00-14:30:00", "14:30:00-17:00:00"]
})

# Creating sample data for Vehicle_Information
vehicle_information = pd.DataFrame({
    "Vehicle Type": ["3W", "4W-EV", "4W"],
    "Number": [50, 25, "Any"],
    "Shipments_Capacity": [5, 8, 25],
    "Max Trip Radius (in KM)": [15, 20, "Any"]
})

# Creating sample data for Store_Location
store_location = pd.DataFrame({
    "Latitute": [19.075887],
    "Longitude": [72.877911]
})

# Save to Excel file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, "../../data")
file_path = os.path.join(DATA_FOLDER, "sample_data.xlsx")
with pd.ExcelWriter(file_path) as writer:
    shipments_data.to_excel(writer, sheet_name="Shipments_Data", index=False)
    vehicle_information.to_excel(writer, sheet_name="Vehicle_Information", index=False)
    store_location.to_excel(writer, sheet_name="Store_Location", index=False)

file_path
