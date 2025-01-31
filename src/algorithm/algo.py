import requests
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from scipy.spatial.distance import pdist, squareform
from scipy.sparse.csgraph import minimum_spanning_tree
import folium
import logging
from data import read_Shipment_data, read_Store_Location, read_Vehical_Information

class SmartRouteOptimizer:
    def __init__(self, logging_level=logging.INFO):
        """
        Initialize the optimizer with configurable logging and robust error handling
        """
        logging.basicConfig(level=logging_level, 
                            format='%(asctime)s - %(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Configuration constants
        self.DELIVERY_TIME_PER_SHIPMENT = 10  # mins
        self.TRAVEL_TIME_PER_KM = 5  # mins
        self.CAPACITY_UTILIZATION_THRESHOLD = 0.5  # 50% vehicle capacity
        self.TRIP_TIME_LIMIT = 120  # max trip time in minutes (example: 2 hours)
        
        # Initialize placeholders
        self.shipments = None
        self.vehicles = None
        self.store = None
        self.processed_shipments = None
        self.priority_vehicles = None
        
    def load_data(self):
        """
        Load and validate shipment, vehicle, and store data
        """
        try:
            self.shipments = read_Shipment_data().dropna()
            self.vehicles = read_Vehical_Information().dropna()
            self.store = read_Store_Location().dropna().iloc[0]
            
            # Validate loaded data
            assert not self.shipments.empty, "No shipment data available"
            assert not self.vehicles.empty, "No vehicle data available"
            
            # Normalize column names to handle potential variations
            self.vehicles.columns = [col.lower().replace(' ', '_') for col in self.vehicles.columns]
            
            self.logger.info(f"Loaded {len(self.shipments)} shipments and {len(self.vehicles)} vehicle types")
            return self
        
        except Exception as e:
            self.logger.error(f"Data loading error: {e}")
            raise
    
    def preprocess_data(self):
        """
        Advanced data preprocessing with route distance calculation
        """
        try:
            shipment_info = []
            for _, row in self.shipments.iterrows():
                # Calculate route data 
                distance = self._calculate_haversine_distance(
                    self.store['Latitute'], self.store['Longitude'], 
                    row['Latitude'], row['Longitude']
                )
                
                shipment_info.append({
                    'Shipment ID': row['Shipment ID'],
                    'Distance': distance,
                    'Time Slot Start': int(row['Delivery Timeslot'].split('-')[0].split(':')[0]),
                    'Time Slot End': int(row['Delivery Timeslot'].split('-')[1].split(':')[0])
                })
            
            self.processed_shipments = pd.merge(
                self.shipments, 
                pd.DataFrame(shipment_info), 
                on='Shipment ID'
            )
            
            # Prioritize vehicles, handling column name variations
            self.priority_vehicles = self.vehicles[
                self.vehicles['vehicle_type'].isin(['3W', '4W-EV'])
            ].sort_values('shipments_capacity', ascending=False)
            
            # Logging preprocessing insights
            self.logger.info(f"Preprocessed {len(self.processed_shipments)} shipments")
            return self
        
        except Exception as e:
            self.logger.error(f"Data preprocessing error: {e}")
            raise
    
    def _calculate_haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate approximate distance between two geographical points
        """
        R = 6371  # Earth's radius in kilometers
        
        # Convert latitude and longitude to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return R * c
    
    def optimize_trips(self):
        """Advanced trip optimization with multiple constraints
        """
        try:
            # Cluster shipments using KMeans
            X = self.processed_shipments[['Latitude', 'Longitude']].values
            n_clusters = max(1, len(X) // 5)  # Adaptive clustering
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            self.processed_shipments['Cluster'] = kmeans.fit_predict(X)
            
            trips = []
            
            for cluster_id in self.processed_shipments['Cluster'].unique():
                cluster_data = self.processed_shipments[
                    self.processed_shipments['Cluster'] == cluster_id
                ]
                
                # Try to assign vehicle, prioritizing 3W and 4W-EV
                trip = self._assign_vehicle_to_cluster(cluster_data)
                if trip:
                    trips.append(trip)
        
            # Create a final dataframe with the desired columns
            trips_df = pd.DataFrame(trips)
            
            # Flatten the trip details for each shipment
            shipment_rows = []
            for _, trip in trips_df.iterrows():
                cluster_data = self.processed_shipments[
                    self.processed_shipments['Shipment ID'].isin(trip['Shipments'])  # No eval(), just a list
                ]
                
                for _, shipment in cluster_data.iterrows():
                    shipment_row = {
                        'TRIP ID': trip['Trip_ID'],
                        'Shipment ID': shipment['Shipment ID'],
                        'Latitude': shipment['Latitude'],
                        'Longitude': shipment['Longitude'],
                        'TIME SLOT': f"{shipment['Time Slot Start']} - {shipment['Time Slot End']}",
                        'Shipments': ', '.join(map(str, trip['Shipments'])),
                        'MST_DIST': trip['Total_Distance'],  # Minimum Spanning Tree distance
                        'TRIP_TIME': round(trip['Total_Distance'] * self.TRAVEL_TIME_PER_KM, 2),
                        'Vehicle_Type': trip['Vehicle_Type'],
                        'CAPACITY_UTI': trip['Capacity_Utilization'],
                        'TIME_UTI': trip['Time_Utilization'],
                        'COV_UTI': 'N/A'  # Assuming this needs to be calculated or assigned elsewhere
                    }
                    shipment_rows.append(shipment_row)
            
            final_df = pd.DataFrame(shipment_rows)
            #print(final_df)
            return final_df
        
        except Exception as e:
            self.logger.error(f"Trip optimization error: {e}")
            raise

    
    def _assign_vehicle_to_cluster(self, cluster_data):
        """
        Vehicle assignment with sophisticated constraint checking
        """
        # Calculate cluster metrics
        num_shipments = len(cluster_data)
        cluster_points = cluster_data[['Latitude', 'Longitude']].values
        
        # Distance calculation (using store as reference)
        store_point = (self.store['Latitute'], self.store['Longitude'])
        distances = [self._calculate_haversine_distance(store_point[0], store_point[1], 
                                                        point[0], point[1]) for point in cluster_points]
        
        total_distance = sum(distances)
        
        # Time slot constraints
        earliest_start = cluster_data['Time Slot Start'].min()
        latest_end = cluster_data['Time Slot End'].max()
        available_time = (latest_end - earliest_start) * 60  # minutes
        
        # Vehicle selection prioritizing 3W and 4W-EV
        for _, vehicle in self.priority_vehicles.iterrows():
            # Constraint validation
            if (num_shipments <= vehicle['shipments_capacity'] and
                (num_shipments / vehicle['shipments_capacity']) >= self.CAPACITY_UTILIZATION_THRESHOLD and
                total_distance <= vehicle['max_trip_radius_(in_km)']):
                
                # Sort shipments by time slot and distance
                sorted_shipments = cluster_data.sort_values(by=['Time Slot Start', 'Distance'])
                
                return {
                    'Trip_ID': f"Trip_{cluster_data['Cluster'].iloc[0]}",
                    'Shipments': sorted_shipments['Shipment ID'].tolist(),
                    'Vehicle_Type': vehicle['vehicle_type'],
                    'Total_Distance': round(total_distance, 2),
                    'Capacity_Utilization': f"{(num_shipments / vehicle['shipments_capacity']):.0%}",
                    'Time_Utilization': f"{(total_distance * self.TRAVEL_TIME_PER_KM / available_time):.0%}"
                }
        
        return None
    
    def plot_shipments_on_map(self):
        """
        Plot shipments and vehicles on a map, color-coded by vehicle type.
        """
        # Initialize a base map centered at the store's location
        base_map = folium.Map(location=[self.store['Latitute'], self.store['Longitude']], zoom_start=13)
        
        # Define vehicle types for color-coding
        vehicle_colors = {
            '3W': 'blue',
            '4W-EV': 'green',
            '4W': 'red'
        }
        # Add a marker for the store location
        folium.Marker(
            location=[self.store['Latitute'], self.store['Longitude']],
            popup="Store Location",
            icon=folium.Icon(color='black', icon='info-sign')
        ).add_to(base_map)
        # Plot shipments
        for _, row in self.processed_shipments.iterrows():
            # Create a marker for each shipment
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=f"Shipment ID: {row['Shipment ID']}\nTime Slot: {row['Time Slot Start']} - {row['Time Slot End']}",
                icon=folium.Icon(color='purple', icon='info-sign')
            ).add_to(base_map)
        
        # Plot vehicles' clusters
        for _, trip in self.processed_shipments.groupby('Cluster'):
            # Get vehicle type (for demonstration, we assume '3W' for simplicity)
            assigned_vehicle = self._assign_vehicle_to_cluster(trip)
            
            # Check if a vehicle was assigned; if not, assign a default type ('4W')
            vehicle_type = assigned_vehicle['Vehicle_Type'] if assigned_vehicle else '4W'
            
            # Cluster center (this is the centroid of the cluster)
            cluster_center = trip[['Latitude', 'Longitude']].mean().values
            
            folium.Marker(
                location=[cluster_center[0], cluster_center[1]],
                popup=f"Cluster Center - Vehicle Type: {vehicle_type}",
                icon=folium.Icon(color=vehicle_colors.get(vehicle_type, 'gray'), icon='cloud')
            ).add_to(base_map)

        # Show the map
        base_map.save("shipments_map.html")
        print("Map saved as 'shipments_map.html'. Open the file to view it.")

# Running the optimizer
optimizer = SmartRouteOptimizer()
optimizer.load_data().preprocess_data()
trips_df = optimizer.optimize_trips()
optimizer.plot_shipments_on_map()


