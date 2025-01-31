from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from algo import SmartRouteOptimizer
import os

app = Flask(__name__)

# Enable CORS globally
CORS(app)
@app.route('/api/predict-vehicle', methods=['POST'])
def predict_vehicle():
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['latitude', 'longitude', 'time_slot']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields (latitude, longitude, time_slot)'}), 400

        # Validate coordinate format
        try:
            lat = float(data['latitude'])
            lon = float(data['longitude'])
        except ValueError:
            return jsonify({'error': 'Invalid coordinate format'}), 400

        # Initialize optimizer and load data
        optimizer = SmartRouteOptimizer()
        try:
            optimizer.load_data().preprocess_data()
            # Add this critical line to generate clusters
            optimizer.optimize_trips()  # This creates the Cluster column
        except Exception as e:
            return jsonify({'error': f'Data processing failed: {str(e)}'}), 500

        # Get prediction
        vehicle_type = optimizer.predict_vehicle_allocation(lat, lon, data['time_slot'])

        # Response handling remains the same
        if vehicle_type:
            return jsonify({
                'status': 'success',
                'vehicle_type': vehicle_type,
                'message': 'Vehicle allocated successfully'
            })
            
        return jsonify({
            'status': 'success',
            'vehicle_type': None,
            'message': 'Location too far for available vehicles'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Prediction failed: {str(e)}'
        }), 500
@app.route('/api/optimize-routes', methods=['POST'])
def optimize_routes():
    try:
        shipment_data = request.get_json()

        # Initialize the optimizer
        optimizer = SmartRouteOptimizer()

        # Load and preprocess the data
        optimizer.load_data()  
        optimizer.preprocess_data()

        # Optimize the trips
        optimized_trips = optimizer.optimize_trips()

        optimizer.plot_shipments_on_map(optimized_trips)
        # Move the generated map to the static folder

        # Convert the result into a JSON serializable format
        result = optimized_trips.to_dict(orient='records')
        
        # Return the optimized trips and the map URL
        return jsonify({
            'trips': result,
            'map_url': f'shipments_map.html'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# To run the app
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001)
