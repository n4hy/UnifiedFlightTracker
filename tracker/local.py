import json
import logging
import time
import os
import requests
from .config import load_config

logger = logging.getLogger(__name__)

DEFAULT_PATHS = {
    "dump1090": "/run/dump1090-fa/aircraft.json",
    "dump978": "/run/dump978-fa/aircraft.json"
}

def fetch_json_from_path_or_url(path_or_url):
    """
    Reads JSON from a local file path or a URL.
    """
    try:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            response = requests.get(path_or_url, timeout=2)
            response.raise_for_status()
            return response.json()
        else:
            if os.path.exists(path_or_url):
                with open(path_or_url, 'r') as f:
                    return json.load(f)
    except Exception as e:
        # Debug level because it's common for one of them to be missing
        logger.debug(f"Could not read local data from {path_or_url}: {e}")
    return None

def normalize_local_flight(f, source_name):
    """
    Normalizes a dump1090/978 aircraft object to the internal format.
    """
    # Hex is mandatory
    hex_id = f.get('hex')
    if not hex_id:
        return None

    # Lat/Lon are mandatory for the map
    lat = f.get('lat')
    lon = f.get('lon')
    if lat is None or lon is None:
        return None

    # Handle 'flight' (callsign) - typically has trailing spaces in dump1090
    callsign = f.get('flight', '').strip() or hex_id

    # Timestamp: dump1090 uses 'now' in root, but 'seen' (age) in aircraft object
    # usually we calculate timestamp = now - seen
    # But here we'll just use current time if not provided, or handle in caller
    # Let's assume the caller passes the 'now' timestamp from the file,
    # and we subtract 'seen'.

    return {
        "source": source_name,
        "hex_id": hex_id.lower(),
        "callsign": callsign,
        "lat": lat,
        "lon": lon,
        "heading": f.get('track', 0),
        "altitude": f.get('alt_baro', f.get('alt_geom', 0)),
        "speed": f.get('gs', 0),
        "type": f.get('category', 'Unknown'), # dump1090 usually just gives category code like 'A0'
        "timestamp": 0 # Placeholder, calculated in fetch function
    }

def fetch_local_data():
    """
    Fetches data from dump1090 and dump978 sources.
    Returns: (list of normalized flights, list of error messages)
    """
    config = load_config()
    local_conf = config.get('local_sources', {})

    # Use config paths or defaults
    path_1090 = local_conf.get('dump1090', DEFAULT_PATHS['dump1090'])
    path_978 = local_conf.get('dump978', DEFAULT_PATHS['dump978'])

    flights = []
    errors = []

    # Fetch dump1090
    data_1090 = fetch_json_from_path_or_url(path_1090)
    if data_1090:
        now_ts = data_1090.get('now', time.time())
        for f in data_1090.get('aircraft', []):
            # Skip if seen > 60 seconds ago (stale)
            seen = f.get('seen', 999)
            if seen > 60: continue

            norm = normalize_local_flight(f, "Local (1090)")
            if norm:
                norm['timestamp'] = int(now_ts - seen)
                flights.append(norm)

    # Fetch dump978
    data_978 = fetch_json_from_path_or_url(path_978)
    if data_978:
        now_ts = data_978.get('now', time.time())
        for f in data_978.get('aircraft', []):
            seen = f.get('seen', 999)
            if seen > 60: continue

            norm = normalize_local_flight(f, "Local (978)")
            if norm:
                norm['timestamp'] = int(now_ts - seen)
                flights.append(norm)

    # If we found nothing and paths don't exist, we don't necessarily error loudly
    # as this is running alongside other sources. But if configured explicitly, maybe?
    # For now, no errors returned to UI to avoid clutter if user doesn't have local running.

    return flights, []
