import requests
import pandas as pd
from data import read_Shipment_data, read_Vehical_Information, read_Store_Location
from polyline import codec
from sklearn.cluster import KMeans  # Importing KMeans for clustering
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# ---------------------------
# Data Loading and Preparation
# ---------------------------

def load_data():
    shipments = read_Shipment_data()
    vehicles = read_Vehical_Information()
    store = read_Store_Location().iloc[0]  # Assuming the first store entry
    print(vehicles.columns)  # Debugging to ensure the 'Vehicle Type' column exists
    return shipments, vehicles, store

def preprocess_data(shipments, store):
    # Calculate route distance for each shipment from the store using GraphHopper
    shipment_distances = []
    for _, row in shipments.iterrows():
        shipment_id = row['Shipment ID']
        shipment_lat, shipment_lon = row['Latitude'], row['Longitude']
        distance = get_route_distance(store['Latitute'], store['Longitude'], shipment_lat, shipment_lon)
        shipment_distances.append({'Distance': distance, 'Shipment ID': shipment_id})
    
    shipments['Distance_from_Store'] = pd.Series([entry['Distance'] for entry in shipment_distances])
    
    # Handle missing or incorrect columns in the vehicle data
    if 'Vehicle Type' not in vehicles.columns:
        print("Missing 'Vehicle Type' column. Assigning default values.")
        vehicles['Vehicle Type'] = 'Unknown'  # Default value for missing 'Vehicle Type'
    
    return shipments, vehicles

def get_route_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the route distance between two points using GraphHopper API.
    """
    # GraphHopper API URL
    api_key = 'your_api_key_here'  # Replace with your actual GraphHopper API key
    url = 'https://graphhopper.com/api/1/route'
    
    params = {
        'point': [f'{lat1},{lon1}', f'{lat2},{lon2}'],  # Correcting multiple 'point' values into a list
        'vehicle': 'car',  # Use 'car', 'bike', or 'foot' based on the type
        'key': 'your api key '
    }
    
    # Sending GET request to GraphHopper API
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Error: Unable to fetch route. Status Code: {response.status_code}")
        return None
    
    data = response.json()
    #print(data)
    
    if 'paths' not in data or not data['paths']:
        print("Error: No paths found in the response.")
        return None
    
    # Extract the distance from the response (distance is in meters, so we convert it to kilometers)
    route = data['paths'][0]
    distance = route['distance'] / 1000  # Convert meters to kilometers
    #print(distance)
    return distance

# ---------------------------
# Feature Engineering and ML Model
# ---------------------------

def prepare_ml_data(shipments, vehicles):
    """
    Prepares the feature set for machine learning model.
    Includes distance from the store, vehicle capacities, and vehicle type.
    """
    shipments['Vehicle_Type'] = vehicles['Vehicle Type']
    shipments['Vehicle_Capacity'] = vehicles['Shipments_Capacity']
    # Other features we need to add: time slots, shipment weight, etc.
    # For now, let's use distance and capacity as features.
    X = shipments[['Distance_from_Store', 'Vehicle_Capacity']]  # Example features
    y = shipments['Shipment ID']  # Target variable: Shipment ID for assignment
    
    return X, y

def train_model(X, y):
    """
    Trains a KMeans model to cluster shipments to vehicles based on distance and capacity.
    """
    # Train-test split for evaluation (optional)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Initialize KMeans model (or another model)
    model = KMeans(n_clusters=3, random_state=42) # because we have three vehicles
    model.fit(X_train)
    
    # Predict on test set
    y_pred = model.predict(X_test)
    
    # Calculate model performance (optional)
    mse = mean_squared_error(y_test, y_pred)
    print(f'Mean Squared Error: {mse}')
    
    return model

def predict_assignments(model, shipments, vehicles):
    """
    Predicts vehicle assignments based on the trained model.
    """
    shipments['Predicted_Vehicle_ID'] = model.predict(shipments[['Distance_from_Store', 'Vehicle_Capacity']])
    assignments = shipments[['Shipment ID', 'Predicted_Vehicle_ID']]
    return assignments

# ---------------------------
# Main Optimization Process 
# ---------------------------

if __name__ == "__main__":
    try:
        shipments, vehicles, store = load_data()
        processed_shipments, vehicles = preprocess_data(shipments, store)
        
        # Prepare data for ML model
        X, y = prepare_ml_data(processed_shipments, vehicles)
        
        # Train the model
        model = train_model(X, y)
        
        # Predict vehicle assignments for shipments
        assignments = predict_assignments(model, processed_shipments, vehicles)
        
        # Output predictions
        print(assignments)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Please check data formats and file paths")
