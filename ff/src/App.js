import React, { useEffect, useState } from 'react';
import './App.css';

const OptimizedRoutes = () => {
  const [trips, setTrips] = useState([]);
  const [filteredTrips, setFilteredTrips] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);

  // Input fields
  const [longitude, setLongitude] = useState('');
  const [latitude, setLatitude] = useState('');
  const [time_slot, settime_slot] = useState('');
  const [vehicleType, setVehicleType] = useState('');

  useEffect(() => {
    fetchOptimizedRoutes();
  }, []);

  const fetchOptimizedRoutes = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/optimize-routes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });

      const data = await response.json();
      if (response.ok) {
        setTrips(data.trips);
        setFilteredTrips(data.trips); // Initialize with all trips
      } else {
        console.error('Failed to fetch optimized routes');
      }
    } catch (error) {
      console.error('Error fetching optimized routes:', error);
    }
  };

  const handleFilterChange = (type, value) => {
    if (type === 'vehicleType') setVehicleType(value);

    const filtered = trips.filter(trip => {
      const matchVehicleType = vehicleType
        ? trip['Vehicle_Type']?.trim().toLowerCase().includes(vehicleType.trim().toLowerCase())
        : true;

      return matchVehicleType;
    });

    setFilteredTrips(filtered);
  };

  const generateGoogleMapsLink = (startLat, startLon, endLat, endLon) => {
    return `https://www.google.com/maps/dir/${startLat},${startLon}/${endLat},${endLon}`;
  };

  const handlePredictVehicle = async () => {
    try {
      setError(null);
      setPrediction(null);
      const body = JSON.stringify({
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        time_slot
      })
      const response = await fetch('http://localhost:5001/api/predict-vehicle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body
      });
      console.log(body)
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Prediction failed');

      setPrediction(data);
    } catch (err) {
      setError(err.message);
    }
  };
  return (
    <div className="optimized-routes-container">
      <h1>Optimized Routes</h1>
         {/* Prediction Section */}
      <div className="prediction-section">
        <h2>New Shipment Prediction</h2>
        <div className="input-group">
          <input
            type="number"
            placeholder="Latitude"
            value={latitude}
            onChange={(e) => setLatitude(e.target.value)}
            step="0.000001"
          />
          <input
            type="number"
            placeholder="Longitude"
            value={longitude}
            onChange={(e) => setLongitude(e.target.value)}
            step="0.000001"
          />
          <input
            type="text"
            placeholder="Time Slot (e.g., 9-12)"
            value={time_slot}
            onChange={(e) => settime_slot(e.target.value)}
          />
          <button onClick={handlePredictVehicle}>Predict Vehicle</button>
        </div>

        {error && <div className="error-message">Error: {error}</div>}
        {prediction && (
          <div className="prediction-result">
            {prediction.vehicle_type ? (
              <>
                <h3>Recommended Vehicle: {prediction.vehicle_type}</h3>
                <p>This vehicle can handle your shipment within the specified time window</p>
              </>
            ) : (
              <h3 className="warning">No suitable vehicle found - location is too far</h3>
            )}
          </div>
        )}
      </div>

      {/* Filtering Inputs */}
      <div className="input-form">
        <div>
          <h1>FILTER</h1>
        </div>
        <label htmlFor="vehicle-type">Vehicle Type:</label>
        <input
          type="text"
          id="vehicle-type"
          value={vehicleType}
          onChange={(e) => handleFilterChange('vehicleType', e.target.value)}
          placeholder="Enter Vehicle Type"
        />
      </div>

      {/* Trip Details Table */}
      <h2>Trip Details</h2>
      <table className="trip-details-table">
        <thead>
          <tr>
            <th>Trip ID</th>
            <th>Shipment IDs</th>
            <th>TIME SLOT</th>
            <th>TRIP_TIME</th>
            <th>FROM(STORE)</th>
            <th>TO (Lat, Long)</th>
            <th>Vehicle Type</th>
            <th>Distance (km)</th>
            <th>Capacity Utilization</th>
            <th>Time Utilization</th>
            <th>Map</th>
          </tr>
        </thead>
        <tbody>
          {filteredTrips.map((trip) => (
            <tr key={trip['TRIP ID']}>
              <td>{trip['TRIP_ID']}</td>
              <td>{trip['Shipments']}</td>
              <td>{trip['TIME_SLOT']}</td>
              <td>{trip['TRIP_TIME']}</td>
              <td>{'19.075887,72.877911'}</td>
              <td>{`${trip['Latitude']},${trip['Longitude']}`}</td>
              <td>{trip['Vehicle_Type']}</td>
              <td>{trip['MST_DIST']}</td>
              <td>{trip['CAPACITY_UTI']}</td>
              <td>{trip['TIME_UTI']}</td>
              <td>
                <a href={generateGoogleMapsLink('19.075887', '72.877911', trip['Latitude'], trip['Longitude'])} target="_blank" rel="noopener noreferrer">
                  View Map
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Map */}
      <h2>Optimized Routes Map</h2>
      <div className="map-container">
        <iframe src="/shipments_map.html" title="Optimized Routes Map" width="100%" height="600px" />
      </div>
    </div>
  );
};

export default OptimizedRoutes;
