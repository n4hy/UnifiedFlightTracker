import logging
from flask import Flask, render_template, request, jsonify
from tracker.config import load_config
from tracker.api import fetch_flightaware, fetch_flightradar24
from tracker.local import fetch_local_data
from tracker.core import deconflict_data
from tracker.geo import haversine_distance

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    config = load_config()
    return render_template('index.html',
                          api_key=config['api_keys'].get('google_maps', ''),
                          map_id=config['api_keys'].get('map_id', 'DEMO_MAP_ID'),
                          default_lat=config['observer']['latitude'],
                          default_lon=config['observer']['longitude'],
                          default_radius=config['observer']['radius_nm'])

@app.route('/api/flights')
def get_flights():
    # Load config (cached)
    config = load_config()

    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        radius = float(request.args.get('radius'))
    except (TypeError, ValueError):
        return jsonify({"flights": [], "messages": ["Invalid parameters"]}), 400

    local_data, local_errors = fetch_local_data()
    fa_data, fa_errors = fetch_flightaware(lat, lon, radius)
    fr24_data, fr24_errors = fetch_flightradar24(lat, lon, radius)

    clean_data = deconflict_data(fa_data, fr24_data, local_data)

    # Calculate distance for each flight
    for f in clean_data:
        if f['lat'] is not None and f['lon'] is not None:
             f['distance_from_obs'] = haversine_distance(lat, lon, f['lat'], f['lon'])
        else:
             f['distance_from_obs'] = float('inf')

    return jsonify({"flights": clean_data, "messages": local_errors + fa_errors + fr24_errors})

if __name__ == '__main__':
    config = load_config()

    # Check Google Maps Key status for user debugging
    gmap_key = config['api_keys'].get('google_maps', '')
    if not gmap_key or "YOUR_" in gmap_key:
        logger.warning("Google Maps API Key is missing or set to default! Map will not load.")
    else:
        masked_key = f"{gmap_key[:4]}...{gmap_key[-4:]}" if len(gmap_key) > 8 else "***"
        logger.info(f"Loaded Google Maps API Key: {masked_key}")

    host = config['server']['host']
    port = config['server']['port']
    logger.info(f"Starting Flight Tracker on http://{host}:{port}")
    app.run(host=host, port=port, debug=True)
