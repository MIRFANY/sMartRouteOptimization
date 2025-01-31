import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from scipy.spatial.distance import pdist, squareform
from scipy.sparse.csgraph import minimum_spanning_tree
import folium
import logging
from data import Read_Output_data, read_Shipment_data, read_Store_Location, read_Vehical_Information, write_output_data

class SmartRouteOptimizer:
    def __init__(self, logging_level=logging.INFO):
        logging.basicConfig(level=logging_level, 
                          format='%(asctime)s - %(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Configuration constants
        self.DELIVERY_TIME_PER_SHIPMENT = 10  # mins
        self.TRAVEL_TIME_PER_KM = 5  # mins
        self.CAPACITY_UTILIZATION_THRESHOLD = 0.5
        self.TRIP_TIME_LIMIT = 120
        
        # Initialize placeholders
        self.shipments = None
        self.vehicles = None
        self.store = None
        self.processed_shipments = None
        self.priority_vehicles = None
        self.trips_df = None

    def load_data(self):
        try:
            self.shipments = read_Shipment_data().dropna()
            self.vehicles = read_Vehical_Information().dropna()
            self.store = read_Store_Location().dropna().iloc[0]
            
            # Clean vehicle data: convert numeric columns
            self.vehicles.columns = [col.lower().replace(' ', '_') for col in self.vehicles.columns]
            numeric_cols = ['max_trip_radius_(in_km)', 'shipments_capacity']
            for col in numeric_cols:
                self.vehicles[col] = pd.to_numeric(self.vehicles[col], errors='coerce')
            
            # Drop vehicles with invalid numeric data
            self.vehicles = self.vehicles.dropna(subset=numeric_cols)
            
            assert not self.shipments.empty, "No shipment data available"
            assert not self.vehicles.empty, "No vehicle data available"
            
            self.logger.info(f"Loaded {len(self.shipments)} shipments and {len(self.vehicles)} vehicle types")
            return self
        
        except Exception as e:
            self.logger.error(f"Data loading error: {e}")
            raise

    def preprocess_data(self):
        try:
            shipment_info = []
            for _, row in self.shipments.iterrows():
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
            
            self.priority_vehicles = self.vehicles[
                self.vehicles['vehicle_type'].isin(['3W', '4W-EV'])
            ].sort_values('shipments_capacity', ascending=False)
            
            self.logger.info(f"Preprocessed {len(self.processed_shipments)} shipments")
            return self
        
        except Exception as e:
            self.logger.error(f"Data preprocessing error: {e}")
            raise

    def _calculate_haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        return R * 2 * np.arcsin(np.sqrt(a))

    def _calculate_mst_distance(self, cluster_data):
        try:
            if len(cluster_data) < 2:
                return 0

            coords = cluster_data[['Latitude', 'Longitude']].values
            dist_matrix = squareform(pdist(coords, metric='euclidean'))
            mst = minimum_spanning_tree(dist_matrix)
            return round(mst.toarray().sum(), 2)

        except Exception as e:
            self.logger.error(f"Error calculating MST distance: {e}")
            return 0

    def optimize_trips(self):
        try:
            X = self.processed_shipments[['Latitude', 'Longitude']].values
            n_clusters = max(1, len(X) // 5)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            self.processed_shipments['Cluster'] = kmeans.fit_predict(X)
            
            trips = []
            for cluster_id in self.processed_shipments['Cluster'].unique():
                cluster_data = self.processed_shipments[
                    self.processed_shipments['Cluster'] == cluster_id
                ]
                
                trip = self._assign_vehicle_to_cluster(cluster_data)
                if trip:
                    total_shipments = len(self.processed_shipments)
                    assigned_shipments = len(trip['Shipments'])
                    cov_uti = f"{(assigned_shipments / total_shipments) * 100:.2f}%" if total_shipments > 0 else "0%"
                    trip["COV_UTI"] = cov_uti
                    trip["Cluster"] = cluster_id  # Store cluster reference
                    trips.append(trip)
        
            self.trips_df = pd.DataFrame(trips)
            shipment_rows = []
            for _, trip in self.trips_df.iterrows():
                cluster_data = self.processed_shipments[
                    self.processed_shipments['Shipment ID'].isin(trip['Shipments'])
                ]
                for _, shipment in cluster_data.iterrows():
                    shipment_rows.append({
                        'TRIP_ID': trip['Trip_ID'],
                        'Shipment_ID': shipment['Shipment ID'],
                        'Latitude': shipment['Latitude'],
                        'Longitude': shipment['Longitude'],
                        'TIME_SLOT': f"{shipment['Time Slot Start']} - {shipment['Time Slot End']}",
                        'Shipments': ', '.join(map(str, trip['Shipments'])),
                        'MST_DIST': trip['Total_Distance'],
                        'TRIP_TIME': round(trip['Total_Distance'] * self.TRAVEL_TIME_PER_KM, 2),
                        'Vehicle_Type': trip['Vehicle_Type'],
                        'CAPACITY_UTI': trip['Capacity_Utilization'],
                        'TIME_UTI': trip['Time_Utilization'],
                        'COV_UTI': trip['COV_UTI']  
                    })
            
            return pd.DataFrame(shipment_rows)
        
        except Exception as e:
            self.logger.error(f"Trip optimization error: {e}")
            raise

    def predict_vehicle_allocation(self, latitude, longitude, time_slot):
        try:
            time_start, time_end = map(int, time_slot.split('-'))
            new_distance = self._calculate_haversine_distance(
                self.store['Latitute'], self.store['Longitude'],
                latitude, longitude
            )

            cluster_id = self._find_nearest_cluster(latitude, longitude)
            cluster_data = self.processed_shipments[
                self.processed_shipments['Cluster'] == cluster_id
            ]

            if self._is_cluster_compatible(cluster_data, time_start, time_end, new_distance):
                vehicle_type = self._get_cluster_vehicle_type(cluster_id)
                if vehicle_type:
                    self.logger.info(f"Using cluster {cluster_id}'s vehicle {vehicle_type}")
                    return vehicle_type

            return self._assign_individual_vehicle(new_distance, time_end - time_start)

        except Exception as e:
            self.logger.error(f"Prediction error: {str(e)}")
            return None

    def _find_nearest_cluster(self, latitude, longitude):
        cluster_centers = self.processed_shipments.groupby('Cluster')[
            ['Latitude', 'Longitude']
        ].mean().values
        
        distances = [
            self._calculate_haversine_distance(latitude, longitude, center[0], center[1])
            for center in cluster_centers
        ]
        return np.argmin(distances)

    def _is_cluster_compatible(self, cluster_data, new_start, new_end, new_distance):
        if cluster_data.empty:
            return False
            
        cluster_start = cluster_data['Time Slot Start'].min()
        cluster_end = cluster_data['Time Slot End'].max()
        cluster_max_distance = cluster_data['Distance'].max()
        return (new_start <= cluster_end) and (new_end >= cluster_start) and (new_distance <= (cluster_max_distance * 1.5))

    def _get_cluster_vehicle_type(self, cluster_id):
        try:
            if self.trips_df is None or self.trips_df.empty:
                return None
                
            cluster_trips = self.trips_df[self.trips_df['Cluster'] == cluster_id]
            return cluster_trips['Vehicle_Type'].iloc[0] if not cluster_trips.empty else None
        except Exception as e:
            self.logger.warning(f"Vehicle lookup error for cluster {cluster_id}: {str(e)}")
            return None

    def _assign_individual_vehicle(self, distance, time_window_hours):
        try:
            time_window_min = time_window_hours * 60
            required_time = (distance * self.TRAVEL_TIME_PER_KM) + self.DELIVERY_TIME_PER_SHIPMENT

            for _, vehicle in self.priority_vehicles.iterrows():
                max_radius = vehicle['max_trip_radius_(in_km)']
                capacity = vehicle['shipments_capacity']
                
                # Check if vehicle can handle the trip
                if (distance <= max_radius and
                    required_time <= min(time_window_min, self.TRIP_TIME_LIMIT)):
                    return vehicle['vehicle_type']
            
            # Fallback to other vehicles
            for _, vehicle in self.vehicles.iterrows():
                max_radius = vehicle['max_trip_radius_(in_km)']
                if distance <= max_radius:
                    return vehicle['vehicle_type']
            
            return None
        except Exception as e:
            self.logger.error(f"Vehicle assignment error: {str(e)}")
            return None
    def predict_vehicle_allocation(self, latitude, longitude, time_slot):
        """Predict suitable vehicle for a new shipment"""
        try:
            # Convert inputs to proper types
            lat = float(latitude)
            lon = float(longitude)
            
            # Calculate distance from store
            distance = self._calculate_haversine_distance(
                self.store['Latitute'], 
                self.store['Longitude'],
                lat,
                lon
            )
            
            # Find best cluster match
            cluster_id = self._find_nearest_cluster(lat, lon)
            cluster_data = self.processed_shipments[
                self.processed_shipments['Cluster'] == cluster_id
            ]
            
            # Check cluster compatibility
            time_start, time_end = map(int, time_slot.split('-'))
            if self._is_cluster_compatible(cluster_data, time_start, time_end, distance):
                vehicle = self._get_cluster_vehicle_type(cluster_id)
                if vehicle:
                    return vehicle
                    
            # Fallback to individual vehicle assignment
            return self._assign_individual_vehicle(distance, time_end - time_start)
            
        except Exception as e:
            self.logger.error(f"Prediction failed: {str(e)}")
            return None    
    def _assign_vehicle_to_cluster(self, cluster_data):
        try:
            num_shipments = len(cluster_data)
            store_point = (self.store['Latitute'], self.store['Longitude'])
            distances = [self._calculate_haversine_distance(store_point[0], store_point[1], 
                                                        point[0], point[1]) for point in cluster_data[['Latitude', 'Longitude']].values]
            total_distance = sum(distances)
            
            earliest_start = cluster_data['Time Slot Start'].min()
            latest_end = cluster_data['Time Slot End'].max()
            available_time = (latest_end - earliest_start) * 60

            for _, vehicle in self.priority_vehicles.iterrows():
                # Convert to float explicitly
                max_radius = float(vehicle['max_trip_radius_(in_km)'])
                capacity = float(vehicle['shipments_capacity'])
                
                if (num_shipments <= capacity and
                    (num_shipments / capacity) >= self.CAPACITY_UTILIZATION_THRESHOLD and
                    total_distance <= max_radius):
                    
                    sorted_shipments = cluster_data.sort_values(by=['Time Slot Start', 'Distance'])
                    return {
                        'Trip_ID': f"Trip_{cluster_data['Cluster'].iloc[0]}",
                        'Shipments': sorted_shipments['Shipment ID'].tolist(),
                        'Vehicle_Type': vehicle['vehicle_type'],
                        'Total_Distance': round(total_distance, 2),
                        'Capacity_Utilization': f"{(num_shipments / capacity):.0%}",
                        'Time_Utilization': f"{(total_distance * self.TRAVEL_TIME_PER_KM / available_time):.0%}" if available_time > 0 else "0%",
                        'Cluster': cluster_data['Cluster'].iloc[0]
                    }
            return None
        except Exception as e:
            self.logger.error(f"Cluster vehicle assignment error: {str(e)}")
            return None

    def plot_shipments_on_map(self, trips_df):
        base_map = folium.Map(location=[self.store['Latitute'], self.store['Longitude']], zoom_start=13)
        folium.Marker(
            location=[self.store['Latitute'], self.store['Longitude']],
            popup="Store Location",
            icon=folium.Icon(color='black', icon='info-sign')
        ).add_to(base_map)
        
        vehicle_colors = {'3W': 'blue', '4W-EV': 'green', '4W': 'red'}
        for _, trip in trips_df.iterrows():
            shipment_coords = []
            for shipment_id in trip['Shipments'].split(', '):
                shipment = self.processed_shipments[self.processed_shipments['Shipment ID'] == int(shipment_id)]
                if not shipment.empty:
                    shipment_coords.append([shipment['Latitude'].values[0], shipment['Longitude'].values[0]])
            
            route_coords = [[self.store['Latitute'], self.store['Longitude']]] + shipment_coords
            folium.PolyLine(route_coords, color=vehicle_colors.get(trip['Vehicle_Type'], 'gray'), 
                          weight=5, opacity=0.7).add_to(base_map)
            folium.Marker(
                location=route_coords[-1],
                popup=f"Trip ID: {trip['TRIP_ID']}<br>Vehicle: {trip['Vehicle_Type']}",
                icon=folium.Icon(color=vehicle_colors.get(trip['Vehicle_Type'], 'gray'), icon='cloud')
            ).add_to(base_map)

        base_map.save("optimized_routes_map.html")
        print("Map saved as 'optimized_routes_map.html'")

if __name__ == "__main__":
    try:
        optimizer = SmartRouteOptimizer(logging_level=logging.DEBUG)
        optimizer.load_data().preprocess_data()
        trips_df = optimizer.optimize_trips()
        write_output_data(trips_df)
        Read_Output_data()
        
        optimizer.plot_shipments_on_map(trips_df)
        
        # Test prediction with enhanced error handling
        test_coords = [
            (19.075887, 72.850804, "9-12"),  # Mumbai
            (19.0962184,72.9124746, "9-12"),    
            (12.9716, 77.5946, "10-14")   
        ]
        
        for lat, lon, slot in test_coords:
            vehicle = optimizer.predict_vehicle_allocation(lat, lon, slot)
            print(f"Prediction for ({lat}, {lon}) @ {slot}: {vehicle}")
            
    except Exception as e:
        print(f"Critical error in main execution: {str(e)}")