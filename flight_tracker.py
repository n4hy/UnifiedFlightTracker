import json
import math
import time
import requests
import threading
import os
import yaml 
from datetime import datetime, timezone
from flask import Flask, render_template_string, request, jsonify

# ==============================================================================
# CONFIGURATION MANAGEMENT
# ==============================================================================
CONFIG_FILE = 'config.yaml'

DEFAULT_CONFIG = {
    "api_keys": {
        "flightaware": "YOUR_FLIGHTAWARE_API_KEY",
        "flightradar24": "YOUR_FR24_API_TOKEN",
        "google_maps": "YOUR_GOOGLE_MAPS_API_KEY"
    },
    "observer": {
        "latitude": 39.8729,
        "longitude": -75.2437,
        "radius_nm": 50
    },
    "server": {
        "host": "0.0.0.0",
        "port": 5000
    }
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'w') as f:
                yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
            return DEFAULT_CONFIG
        except Exception as e:
            return DEFAULT_CONFIG
    else:
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = yaml.safe_load(f)
                if not config: return DEFAULT_CONFIG
                for section in DEFAULT_CONFIG:
                    if section not in config:
                        config[section] = DEFAULT_CONFIG[section]
                return config
        except Exception as e:
            return DEFAULT_CONFIG

APP_CONFIG = load_config()

# ==============================================================================
# HELPERS
# ==============================================================================
def get_bounding_box(lat, lon, radius_nm):
    R = 3440.065
    max_lat = lat + math.degrees(radius_nm / R)
    min_lat = lat - math.degrees(radius_nm / R)
    max_lon = lon + math.degrees(radius_nm / R / math.cos(math.radians(lat)))
    min_lon = lon - math.degrees(radius_nm / R / math.cos(math.radians(lat)))
    return round(min_lat, 4), round(max_lat, 4), round(min_lon, 4), round(max_lon, 4)

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 3440.065 
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def parse_fa_time(iso_str):
    try:
        dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except:
        return int(time.time())

# ==============================================================================
# DATA INGESTION
# ==============================================================================
def fetch_flightaware(lat, lon, radius_nm):
    api_key = APP_CONFIG['api_keys'].get('flightaware')
    if not api_key or "YOUR_" in api_key:
        return [], ["FlightAware Key is default/missing"]

    min_lat, max_lat, min_lon, max_lon = get_bounding_box(lat, lon, radius_nm)
    url = "https://aeroapi.flightaware.com/aeroapi/flights/search"
    query = f'-latlong "{min_lat} {min_lon} {max_lat} {max_lon}"'
    headers = {"x-apikey": api_key, "Accept": "application/json; charset=UTF-8"}
    params = {"query": query, "max_pages": 1}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        normalized_flights = []
        for f in data.get('flights', []):
            pos = f.get('last_position')
            if not pos: continue 
            
            ident = f.get('ident') or 'Unknown'
            ts = parse_fa_time(pos.get('timestamp'))

            normalized_flights.append({
                "source": "FlightAware",
                "hex_id": ident, 
                "callsign": ident,
                "lat": pos.get('latitude'),
                "lon": pos.get('longitude'),
                "heading": pos.get('heading', 0),
                "altitude": pos.get('altitude', 0) * 100 if pos.get('altitude') else 0,
                "speed": pos.get('groundspeed', 0),
                "type": f.get('aircraft_type', 'Unknown'),
                "timestamp": ts
            })
        return normalized_flights, []

    except Exception as e:
        msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
             msg = f"{e.response.status_code} - Bad Request (Check Query Syntax)"
        return [], [f"FlightAware Error: {msg}"]

def fetch_flightradar24(lat, lon, radius_nm):
    token = APP_CONFIG['api_keys'].get('flightradar24')
    if not token or "YOUR_" in token:
        return [], ["FR24 Token is default/missing"]

    min_lat, max_lat, min_lon, max_lon = get_bounding_box(lat, lon, radius_nm)
    bounds_str = f"{max_lat},{min_lat},{min_lon},{max_lon}"
    url = f"https://fr24api.flightradar24.com/api/live/flight-positions/full?bounds={bounds_str}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Accept-Version": "v1"
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        normalized_flights = []
        for f in data.get('data', []):
            raw_hex = f.get('hex')
            safe_hex = str(raw_hex).lower() if raw_hex else None
            safe_callsign = f.get('callsign') or 'Unknown'
            ts = f.get('updated', int(time.time()))

            normalized_flights.append({
                "source": "Flightradar24",
                "hex_id": safe_hex or safe_callsign,
                "callsign": safe_callsign,
                "lat": f.get('lat'),
                "lon": f.get('lon'),
                "heading": f.get('track', 0),
                "altitude": f.get('alt', 0),
                "speed": f.get('gs', 0),
                "type": f.get('type', 'Unknown'),
                "timestamp": ts
            })
        return normalized_flights, []
        
    except Exception as e:
        msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
             msg = f"{e.response.status_code} - {e.response.text}"
        return [], [f"FR24 Error: {msg}"]

def deconflict_data(fa_data, fr24_data):
    """
    Merges data prioritizing ICAO Hex matching + Spatial backup.
    """
    SPATIAL_THRESHOLD_NM = 6.0 
    
    merged_results = {}
    
    # Index FA Data
    fa_indexed = {}
    def clean_id(f): return str(f['hex_id']).strip().lower()

    for f in fa_data:
        f['_merged'] = False
        fa_indexed[clean_id(f)] = f

    for fr in fr24_data:
        fr_id = clean_id(fr)
        match_found = False
        fa_match = None

        # 1. Exact ICAO Match
        if fr_id in fa_indexed:
            fa_match = fa_indexed[fr_id]
            match_found = True
        else:
            # 2. Spatial Match (if ICAO mismatch)
            closest_dist = float('inf')
            for fa_id, fa in fa_indexed.items():
                if fa.get('_merged'): continue
                if fa['lat'] and fa['lon'] and fr['lat'] and fr['lon']:
                    dist = haversine_distance(fa['lat'], fa['lon'], fr['lat'], fr['lon'])
                    if dist < closest_dist and dist <= SPATIAL_THRESHOLD_NM:
                        closest_dist = dist
                        fa_match = fa
                        match_found = True

        if match_found and fa_match:
            # Timestamp Logic: Keep Freshest Position
            fa_ts = fa_match.get('timestamp', 0)
            fr_ts = fr.get('timestamp', 0)
            
            fa_match['_merged'] = True
            fa_match['source'] = "Merged (FA+FR24)"
            
            if fr_ts >= fa_ts:
                fa_match['lat'] = fr['lat']
                fa_match['lon'] = fr['lon']
                fa_match['heading'] = fr['heading']
                fa_match['altitude'] = fr['altitude']
                fa_match['speed'] = fr['speed']
                fa_match['timestamp'] = fr['timestamp']
            
            merged_results[clean_id(fa_match)] = fa_match
        else:
            merged_results[fr_id] = fr

    for fa in fa_indexed.values():
        if not fa.get('_merged'):
            merged_results[clean_id(fa)] = fa

    # Sort results by Hex ID by default
    sorted_flights = sorted(list(merged_results.values()), key=lambda x: x['hex_id'])
    return sorted_flights

# ==============================================================================
# FLASK APPLICATION
# ==============================================================================
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Unified Flight Tracker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body, html { height: 100%; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; overflow: hidden; }
        
        /* Flex Layout */
        #container { display: flex; height: 100vh; width: 100vw; }
        
        /* Left Dashboard (40%) */
        #dashboard {
            width: 40%;
            height: 100%;
            background: #f8f9fa;
            border-right: 1px solid #ddd;
            display: flex;
            flex-direction: column;
            box-shadow: 2px 0 5px rgba(0,0,0,0.1);
            z-index: 10;
        }

        /* Right Map (60%) */
        #map-wrapper { width: 60%; height: 100%; position: relative; }
        #map { height: 100%; width: 100%; }

        /* Dashboard Components */
        .header { padding: 15px; background: #fff; border-bottom: 1px solid #eee; }
        .controls { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 10px; }
        .controls label { font-size: 12px; font-weight: bold; color: #555; }
        .controls input { width: 100%; padding: 5px; border: 1px solid #ccc; border-radius: 4px; }
        
        button.scan-btn {
            width: 100%; background: #4285F4; color: white; border: none; padding: 8px; 
            border-radius: 4px; cursor: pointer; font-weight: bold; margin-top: 5px;
        }
        button.scan-btn:hover { background: #3367d6; }

        #status { font-size: 12px; color: #666; margin-top: 5px; min-height: 1.2em; }
        .error-text { color: #d93025; font-weight: bold; }

        /* Scrollable Table */
        .table-container {
            flex: 1;
            overflow-y: auto;
            background: white;
            border-top: 1px solid #eee;
        }

        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        
        thead th {
            position: sticky; top: 0; background: #e8eaed; 
            color: #333; padding: 8px; text-align: left; 
            border-bottom: 2px solid #ccc; font-weight: 600;
            cursor: pointer; user-select: none;
        }
        thead th:hover { background-color: #d2e3fc; }
        
        tbody tr { border-bottom: 1px solid #f1f1f1; cursor: pointer; }
        tbody tr:hover { background-color: #e8f0fe; }
        tbody td { padding: 8px; white-space: nowrap; }
        
        /* Column Specifics */
        .col-right { text-align: right; }
        .source-dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 5px; }
        .sort-icon { font-size: 10px; margin-left: 5px; color: #555; }

        /* Scrollbar styling */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #f1f1f1; }
        ::-webkit-scrollbar-thumb { background: #888; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #555; }

    </style>
    <script src="https://maps.googleapis.com/maps/api/js?key={{ api_key }}"></script>
</head>
<body>

<div id="container">
    <div id="dashboard">
        <div class="header">
            <h2 style="margin: 0 0 10px 0; color: #202124;">Flight Tracker</h2>
            <div class="controls">
                <div><label>Lat</label><input type="number" id="obsLat" step="0.0001" value="{{ default_lat }}"></div>
                <div><label>Lon</label><input type="number" id="obsLon" step="0.0001" value="{{ default_lon }}"></div>
                <div><label>Radius (NM)</label><input type="number" id="obsRadius" value="{{ default_radius }}"></div>
            </div>
            <button class="scan-btn" onclick="updateSettings()">Update & Scan</button>
            <div id="status">Ready.</div>
        </div>
        
        <div class="table-container">
            <table id="flightTable">
                <thead>
                    <tr>
                        <th onclick="toggleSort('hex_id')">ICAO <span id="sort-hex_id" class="sort-icon"></span></th>
                        <th onclick="toggleSort('callsign')">Ident <span id="sort-callsign" class="sort-icon"></span></th>
                        <th class="col-right" onclick="toggleSort('altitude')">Alt (ft) <span id="sort-altitude" class="sort-icon"></span></th>
                        <th class="col-right" onclick="toggleSort('speed')">Spd (kts) <span id="sort-speed" class="sort-icon"></span></th>
                        <th class="col-right" onclick="toggleSort('distance_from_obs')">Dist (NM) <span id="sort-distance_from_obs" class="sort-icon"></span></th>
                        <th onclick="toggleSort('source')">Source <span id="sort-source" class="sort-icon"></span></th>
                        <th class="col-right" onclick="toggleSort('heading')">Hdg <span id="sort-heading" class="sort-icon"></span></th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Rows injected here -->
                </tbody>
            </table>
        </div>
    </div>

    <div id="map-wrapper">
        <div id="map"></div>
    </div>
</div>

<script>
    let map;
    let markers = {};
    let rangeCircle;
    let observerMarker; // House icon marker
    let refreshInterval;
    
    // Sort State: { col: string, dir: number } (0: none, 1: asc, 2: desc)
    let sortState = { col: null, dir: 0 };
    let flightCache = [];
    
    const planeIcon = {
        path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
        scale: 4,
        fillColor: "#4285F4",
        fillOpacity: 1,
        strokeWeight: 1,
        rotation: 0
    };

    const houseIcon = {
        // SVG path for a simple house
        path: "M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z",
        fillColor: "#0F9D58", // Green
        fillOpacity: 1,
        strokeWeight: 2,
        strokeColor: "#FFFFFF",
        scale: 1.5,
        anchor: new google.maps.Point(12, 12) // Center the icon roughly
    };

    function initMap() {
        const startPos = { lat: {{ default_lat }}, lng: {{ default_lon }} }; 
        map = new google.maps.Map(document.getElementById("map"), {
            zoom: 9,
            center: startPos,
            mapTypeId: 'terrain',
            streetViewControl: false,
            fullscreenControl: false,
            mapTypeControlOptions: { position: google.maps.ControlPosition.TOP_RIGHT }
        });
        
        drawObserver(startPos.lat, startPos.lng, {{ default_radius }});
        startTracking();
    }

    function updateSettings() {
        const lat = parseFloat(document.getElementById('obsLat').value);
        const lon = parseFloat(document.getElementById('obsLon').value);
        const rad = parseFloat(document.getElementById('obsRadius').value);
        
        map.setCenter({lat: lat, lng: lon});
        drawObserver(lat, lon, rad);
        
        if (refreshInterval) clearInterval(refreshInterval);
        refreshInterval = setInterval(fetchFlights, 10000);
        fetchFlights();
    }

    function drawObserver(lat, lon, radiusNm) {
        const pos = {lat: lat, lng: lon};

        // Draw/Update Range Circle
        if (rangeCircle) rangeCircle.setMap(null);
        const radiusMeters = radiusNm * 1852;
        rangeCircle = new google.maps.Circle({
            strokeColor: "#FF0000", strokeOpacity: 0.8, strokeWeight: 2,
            fillColor: "#FF0000", fillOpacity: 0.05,
            map: map, center: pos, radius: radiusMeters
        });
        map.fitBounds(rangeCircle.getBounds());

        // Draw/Update House Icon
        if (observerMarker) observerMarker.setMap(null);
        observerMarker = new google.maps.Marker({
            position: pos,
            map: map,
            icon: houseIcon,
            title: "Observer Location",
            zIndex: 1000 // Ensure it stays on top of planes
        });
    }

    function startTracking() {
        refreshInterval = setInterval(fetchFlights, 10000);
        fetchFlights();
    }

    async function fetchFlights() {
        const lat = document.getElementById('obsLat').value;
        const lon = document.getElementById('obsLon').value;
        const rad = document.getElementById('obsRadius').value;
        const statusDiv = document.getElementById('status');
        
        // Only show text if table is empty to avoid flicker
        if (flightCache.length === 0) statusDiv.innerHTML = "Fetching data...";

        try {
            const response = await fetch(`/api/flights?lat=${lat}&lon=${lon}&radius=${rad}`);
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                 const errorHtml = data.messages.join(", ");
                 statusDiv.innerHTML = `<span class="error-text">Warnings: ${errorHtml}</span>`;
            } else {
                 statusDiv.innerHTML = `Tracking ${data.flights.length} aircraft. Updated: ${new Date().toLocaleTimeString()}`;
            }
            
            updateMarkers(data.flights);
            flightCache = data.flights; // Store for sorting
            renderTable(); // Render based on cache and sort state
            
        } catch (error) {
            console.error("Error fetching flights:", error);
            statusDiv.innerHTML = "<span class='error-text'>Connection Error. Check console.</span>";
        }
    }

    function updateMarkers(flights) {
        if (!flights) return;
        const currentHexIds = new Set(flights.map(f => f.hex_id));
        
        for (let hex in markers) {
            if (!currentHexIds.has(hex)) {
                markers[hex].setMap(null);
                delete markers[hex];
            }
        }
        flights.forEach(f => {
            const pos = { lat: f.lat, lng: f.lon };
            const icon = { ...planeIcon, rotation: f.heading };
            
            let color = "#4285F4"; // FA Blue
            if (f.source.includes("Merged")) color = "#800080"; // Merged Purple
            else if (f.source === "Flightradar24") color = "#FFD700"; // FR24 Gold
            
            icon.fillColor = color;

            const contentString = `<div style="color:black"><b>${f.callsign}</b><br>Hex: ${f.hex_id}</div>`;

            if (markers[f.hex_id]) {
                markers[f.hex_id].setPosition(pos);
                markers[f.hex_id].setIcon(icon);
                markers[f.hex_id]._infoContent = contentString;
            } else {
                const marker = new google.maps.Marker({ position: pos, map: map, icon: icon, title: f.callsign });
                marker._infoWindow = new google.maps.InfoWindow({ content: contentString });
                marker._infoContent = contentString;
                marker.addListener("click", () => {
                     marker._infoWindow.setContent(marker._infoContent);
                     marker._infoWindow.open(map, marker);
                });
                markers[f.hex_id] = marker;
            }
        });
    }

    // --- SORTING LOGIC ---
    function toggleSort(col) {
        if (sortState.col === col) {
            // Cycle: 0 -> 1 -> 2 -> 0
            sortState.dir = (sortState.dir + 1) % 3;
        } else {
            sortState.col = col;
            sortState.dir = 1; // Default to Asc
        }
        renderTable();
    }

    function renderTable() {
        const tbody = document.querySelector("#flightTable tbody");
        tbody.innerHTML = ""; // Clear existing

        // Create shallow copy for display
        let displayList = [...flightCache];

        // Apply Sort if active (dir 1 or 2)
        if (sortState.dir !== 0 && sortState.col) {
            displayList.sort((a, b) => {
                let v1 = a[sortState.col];
                let v2 = b[sortState.col];
                
                // normalize strings
                if (typeof v1 === 'string') v1 = v1.toLowerCase();
                if (typeof v2 === 'string') v2 = v2.toLowerCase();
                
                // Handle nulls
                if (v1 == null) v1 = -Infinity; // Push nulls to bottom/top
                if (v2 == null) v2 = -Infinity;

                if (v1 < v2) return sortState.dir === 1 ? -1 : 1;
                if (v1 > v2) return sortState.dir === 1 ? 1 : -1;
                return 0;
            });
        }
        // If sortState.dir === 0, we use flightCache 'as is' (Original State from server)

        // Render Rows
        displayList.forEach(f => {
            const tr = document.createElement("tr");
            
            let color = "#4285F4";
            if (f.source.includes("Merged")) color = "#800080";
            else if (f.source === "Flightradar24") color = "#FFD700";
            
            const sourceHtml = `<span class="source-dot" style="background:${color}"></span>${f.source === "Merged (FA+FR24)" ? "Merged" : (f.source === "Flightradar24" ? "FR24" : "FA")}`;

            // Show distance to 1 decimal place, or '-' if invalid
            const distDisplay = (f.distance_from_obs !== undefined && f.distance_from_obs !== Infinity) 
                                ? f.distance_from_obs.toFixed(1) 
                                : "-";

            tr.innerHTML = `
                <td style="font-family:monospace; font-weight:bold;">${f.hex_id.toUpperCase()}</td>
                <td>${f.callsign}</td>
                <td class="col-right">${f.altitude.toLocaleString()}</td>
                <td class="col-right">${Math.round(f.speed)}</td>
                <td class="col-right">${distDisplay}</td>
                <td>${sourceHtml}</td>
                <td class="col-right">${Math.round(f.heading)}°</td>
            `;
            
            // Highlight marker on hover/click
            tr.onclick = () => {
                if (markers[f.hex_id]) {
                    const m = markers[f.hex_id];
                    map.panTo(m.getPosition());
                    m._infoWindow.setContent(m._infoContent);
                    m._infoWindow.open(map, m);
                }
            };
            
            tbody.appendChild(tr);
        });

        // Update Sort Icons
        document.querySelectorAll(".sort-icon").forEach(el => el.innerHTML = "");
        if (sortState.dir !== 0 && sortState.col) {
            const arrow = sortState.dir === 1 ? "▲" : "▼";
            const iconEl = document.getElementById("sort-" + sortState.col);
            if (iconEl) iconEl.innerHTML = arrow;
        }
    }

    window.onload = initMap;
</script>
</body>
</html>
"""

@app.route('/')
def index():
    config = load_config()
    return render_template_string(HTML_TEMPLATE, 
                                  api_key=config['api_keys'].get('google_maps', ''),
                                  default_lat=config['observer']['latitude'],
                                  default_lon=config['observer']['longitude'],
                                  default_radius=config['observer']['radius_nm'])

@app.route('/api/flights')
def get_flights():
    global APP_CONFIG
    APP_CONFIG = load_config()

    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        radius = float(request.args.get('radius'))
    except (TypeError, ValueError):
        return jsonify({"flights": [], "messages": ["Invalid parameters"]}), 400

    fa_data, fa_errors = fetch_flightaware(lat, lon, radius)
    fr24_data, fr24_errors = fetch_flightradar24(lat, lon, radius)
    clean_data = deconflict_data(fa_data, fr24_data)
    
    # Calculate distance for each flight
    for f in clean_data:
        if f['lat'] is not None and f['lon'] is not None:
             f['distance_from_obs'] = haversine_distance(lat, lon, f['lat'], f['lon'])
        else:
             f['distance_from_obs'] = float('inf') 
    
    return jsonify({"flights": clean_data, "messages": fa_errors + fr24_errors})

if __name__ == '__main__':
    host = APP_CONFIG['server']['host']
    port = APP_CONFIG['server']['port']
    print(f"Starting Flight Tracker on http://{host}:{port}")
    app.run(host=host, port=port, debug=True)
