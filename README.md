# SmartRoute Optimizer

## Overview

The **SmartRoute Optimizer** is an AI/ML-based solution designed to optimize delivery routes for grocery and essential item deliveries. The system automates the process of creating and sequencing shipments into delivery trips, considering constraints such as time slots, vehicle capacities, and delivery locations. The goal is to maximize vehicle capacity utilization, minimize the number of trips, reduce overall travel distance, and ensure timely deliveries.

This project leverages machine learning algorithms, geospatial data analysis, and optimization techniques to create efficient delivery routes. The solution is particularly useful for businesses that rely on fast and accurate logistics to meet customer demands.

## Problem Statement

Traditional delivery planning processes are often manual, time-consuming, and prone to inefficiencies. These inefficiencies can lead to increased delivery times, underutilized resources, and higher operational costs. The **SmartRoute Optimizer** addresses these challenges by automating the delivery planning process and optimizing resource allocation.

### Key Objectives

- **Maximize Vehicle Capacity Utilization:** Efficiently use vehicle space to reduce the number of vehicles required for delivery.
- **Minimize the Number of Trips:** Optimize the allocation of shipments to reduce overall delivery trips.
- **Minimize the Overall Distance:** Plan trips to reduce the total distance traveled by vehicles.
- **Ensure Trip Completion Time:** Plan trips within acceptable time limits to meet delivery commitments.
- **Automated Vehicle Type Allocation:** Assign the most appropriate vehicle type based on the number of shipments, prioritizing certain vehicle types (e.g., 3W, 4W-EV).

## Features

- **🚀 AI/ML-Based Trip Optimization:** The system uses clustering algorithms (e.g., K-Means) to group shipments into trips and assigns the most suitable vehicle type based on capacity and distance constraints.
- **🗺️ Interactive Map Visualization:** The optimized routes are displayed on an interactive map using the `folium` library, allowing users to visualize the delivery routes and shipment locations.
- **🚚 Automated Vehicle Allocation:** The system prioritizes the use of specific vehicle types (e.g., 3W, 4W-EV) before assigning regular vehicles, ensuring efficient resource utilization.
- **✅ Trip Validation:** Each trip is validated against constraints such as capacity utilization, time slot utilization, and distance coverage.

## Project Setup

### 📂 Data Files

- **📦 Shipment Data:** Contains details of shipments, including geolocations and delivery timeslots. Located in the `SmartRoute Optimizer.xlsx` file under the `Shipments_Data` sheet.
- **🚗 Vehicle Information:** Contains details of available vehicle types, their shipment capacities, and maximum trip radius. Located in the `SmartRoute Optimizer.xlsx` file under the `Vehicle_Information` sheet.
- **🏬 Store Location:** Contains the geolocation of the store (warehouse) from which shipments are dispatched. Located in the `SmartRoute Optimizer.xlsx` file under the `Store Location` sheet.

### 📌 Assumptions

- **Travel Time per Kilometer:** 5 minutes.
- **Delivery Time per Shipment:** 10 minutes.
- **Trip Time Limit:** 120 minutes.

## How It Works

1. **📊 Data Loading:** The system loads shipment data, vehicle information, and store location from the provided Excel file.
2. **🛠️ Data Preprocessing:** The system calculates the distance between the store and each shipment location using the Haversine formula. It also processes the delivery timeslots and prepares the data for clustering.
3. **📍 Clustering:** The system uses K-Means clustering to group shipments into clusters based on their geolocations.
4. **🚛 Trip Optimization:** For each cluster, the system assigns the most suitable vehicle type based on capacity and distance constraints. It ensures that priority vehicles (e.g., 3W, 4W-EV) are used first.
5. **🗺️ Route Visualization:** The optimized trips are displayed on an interactive map using the `folium` library. Each trip is represented as a route starting and ending at the store, with markers for each shipment location.
6. **📋 Output:** The system generates a tabular representation of each trip, including details such as Trip ID, Shipment Sequence, Assigned Vehicle Type, and validation parameters (e.g., Capacity Utilization, Time Utilization, Distance Coverage).

## 📊 Output Format

The output is a tabular representation of each trip, with the following parameters:

| Trip_ID | Shipment Details | Assigned Vehicle Type | MST_DIST | TRIP_TIME | CAPACITY_UTI | TIME_UTI | COV_UTI |
|---------|----------------|----------------------|---------|----------|--------------|---------|--------|
| 1       | [Seq]         | 4W-EV                | 10km    | 90 min   | 80%          | 75%     | 85%    |

## 🚀 Usage

### Running the Project

1. **Install Dependencies:** Ensure you have the required Python libraries installed. You can install them using the following command:

    ```bash
    pip install pandas numpy scikit-learn folium flask flask-cors xlsxwriter
    ```

2. **Run the API:** Start the Flask API by running the `api.py` file:

    ```bash
    python api.py
    ```

3. **Access the API:** The API will be available at `http://localhost:5001`. You can use the following endpoints:
    - **Predict Vehicle Allocation:** `POST /api/predict-vehicle`
    - **Optimize Routes:** `POST /api/optimize-routes`

4. **View the Map:** The optimized routes will be saved as an HTML file (`optimized_routes_map.html`), which can be opened in a web browser to visualize the routes.

## 📌 Evaluation Criteria

- **✅ Quality and Effectiveness of Solution:** The solution should effectively optimize delivery routes and meet all constraints.
- **🌍 Potential for Real-World Impact:** The solution should demonstrate practical applicability in real-world delivery scenarios.
- **🎬 Presentable Demo:** The project should include a clear and interactive demo showcasing the features and functionality.

## 🔥 Optional Features

- **🚛 Filter Trips by Vehicle Type:** Users can filter and sort trips based on the assigned vehicle type.

## 📜 Documentation

- **📖 User Manual:** A detailed user manual explaining how to set up and use the SmartRoute Optimizer.
- **⚙️ Technical Specifications:** Documentation of the algorithms and methodologies used in the project.
- **🎥 Demo Video:** A short video (2-5 minutes) showcasing the project and its features.

## 🎯 Conclusion

The **SmartRoute Optimizer** is a powerful tool for businesses looking to streamline their delivery operations. By automating the delivery planning process and optimizing resource allocation, the system helps reduce costs, improve efficiency, and enhance customer satisfaction.


