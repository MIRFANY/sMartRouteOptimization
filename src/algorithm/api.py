from flask import Flask, request, jsonify
from algo import SmartRouteOptimizer  # Importing the optimizer class

app = Flask(__name__)

@app.route('/api/optimize-routes', methods=['POST'])
def optimize_routes():
    try:
        # Get the shipment data from the incoming JSON request
        shipment_data = request.get_json()
        
        # Initialize the optimizer
        optimizer = SmartRouteOptimizer()
        
        # Load data (You can modify this to pass the `shipment_data` if needed)
        optimizer.load_data()  # Assuming this uses default internal data loading
        
        # Preprocess the data
        optimizer.preprocess_data()
        
        # Optimize the trips
        optimized_trips = optimizer.optimize_trips()
        
        # Convert the result into a JSON serializable format
        result = optimized_trips.to_dict(orient='records')
        
        return jsonify(result)  # Return the optimized trips as a JSON response
    except Exception as e:
        return jsonify({'error': str(e)}), 400  # Return error message if something goes wrong

if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask app
