import pandas as pd
import os
import folium
import matplotlib.pyplot as plt

# Set up file paths for input and output
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, "../../data")
INPUT_FILE = os.path.join(DATA_FOLDER, "SmartRoute Optimizer.xlsx")
OUT_FILE = os.path.join(DATA_FOLDER, "Sample Output Trip.xlsx")

def read_Shipment_data():
    """Load shipment data from the Excel file."""
    try:
        # Load the Excel file and the 'Shipments_Data' sheet
        xls = pd.ExcelFile(INPUT_FILE)
        Shipment_data = xls.parse("Shipments_Data")
        print(f"✅ Loaded 'Shipments_Data' from {INPUT_FILE}")
        print(Shipment_data.head())  # Print first 5 rows to confirm data
        return Shipment_data
    except Exception as e:
        print(f"❌ Error reading {INPUT_FILE}: {e}")
        return None

def plot_shipment_data_on_map(shipment_data):
    """Plot shipment data on a Folium map."""
    try:
        # Initialize the map centered around the mean of latitude and longitude
        m = folium.Map(location=[shipment_data['Latitude'].mean(), shipment_data['Longitude'].mean()],
                       zoom_start=12, control_scale=True)

        # Add each shipment as a marker on the map
        for _, row in shipment_data.iterrows():
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=f"Shipment ID: {row['Shipment ID']}<br>Delivery Timeslot: {row['Delivery Timeslot']}",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)

        # Save the map as an HTML file
        m.save(os.path.join(DATA_FOLDER, "shipment_map.html"))
        print(f"✅ Map saved to {os.path.join(DATA_FOLDER, 'shipment_map.html')}")
    except Exception as e:
        print(f"❌ Error plotting data on map: {e}")

def read_Vehical_Information():
    sheet_name='Vehicle_Information'
    """Read the vehicle information from the specified sheet."""
    try:
        xls = pd.ExcelFile(INPUT_FILE)
        Vehical_Information = xls.parse(sheet_name)
        print(f"✅ Loaded {sheet_name} from {INPUT_FILE}")
        print(Vehical_Information.head())  
        return Vehical_Information
    except Exception as e:
        print(f"❌ Error reading {INPUT_FILE}: {e}")
        return None

def read_Store_Location():
    sheet_name='Store Location'
    """Read store location data from the specified sheet."""
    try:
        xls = pd.ExcelFile(INPUT_FILE)
        Store_Location = xls.parse(sheet_name)
        print(f"✅ Loaded {sheet_name} from {INPUT_FILE}")
        print(Store_Location.head()) 
        return Store_Location
    except Exception as e:
        print(f"❌ Error reading {INPUT_FILE}: {e}")
        return None
def write_output_data(data):
    """Write the trips DataFrame to the output Excel file."""
    try:
        with pd.ExcelWriter(OUT_FILE, engine='xlsxwriter') as writer:
            data.to_excel(writer, sheet_name='Sample Output Trip', index=False)
            print(f"✅ Output data written to {OUT_FILE}")
    except Exception as e:
        print(f"❌ Error writing output data: {e}")
        
def Read_Output_data():
    sheet_name='Sample Output Trip'
    """Read output data from the specified sheet."""
    try:
        xls = pd.ExcelFile(OUT_FILE)
        Output_data = xls.parse(sheet_name)
        print(f"✅ Loaded {sheet_name} from {OUT_FILE}")
        print(Output_data.head()) 
        return Output_data
    except Exception as e:
        print(f"❌ Error reading {OUT_FILE}: {e}")
        return None

def main():
    """Main function to load data and plot on the map."""
    # Load the shipment data
    shipment_data = read_Shipment_data()
    vehicle_info = read_Vehical_Information()
    store_location = read_Store_Location()
    print(vehicle_info)
    print(store_location)
    if shipment_data is not None:
        plot_shipment_data_on_map(shipment_data)
    else:
        print("❌ Shipment data is not available.")

if __name__ == "__main__":
    # Run the main function
    main()
