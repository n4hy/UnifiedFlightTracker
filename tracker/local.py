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

DEFAULT_URLS = {
    "dump1090": "http://localhost:8080/data/aircraft.json",
    "dump978": "http://localhost:8978/data/aircraft.json" # Common port for skyaware978
}

def fetch_json_from_path_or_url(path_or_url):
    """
    Reads JSON from a local file path or a URL.
    """
    try:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            response = requests.get(path_or_url, timeout=2)
            response.raise_for_status()
            logger.info(f"Successfully fetched local data from URL: {path_or_url}")
            return response.json()
        else:
            if os.path.exists(path_or_url):
                with open(path_or_url, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Successfully fetched local data from file: {path_or_url}")
                    return data
            else:
                logger.debug(f"Local file not found: {path_or_url}")
    except Exception as e:
        logger.warning(f"Failed to read local data from {path_or_url}: {e}")
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

    return {
        "source": source_name,
        "hex_id": hex_id.lower(),
        "callsign": callsign,
        "lat": lat,
        "lon": lon,
        "heading": f.get('track', 0),
        "altitude": f.get('alt_baro', f.get('alt_geom', 0)),
        "speed": f.get('gs', 0),
        "type": f.get('category', 'Unknown'),
        "timestamp": 0 # Placeholder
    }

def fetch_local_data():
    """
    Fetches data from dump1090 and dump978 sources using Path first, then URL fallback.
    """
    config = load_config()
    local_conf = config.get('local_sources', {})

    # 1. Determine Sources for 1090
    # User config takes precedence. If not set, try default path. If that fails, try default URL.
    # Actually, we should just try both defaults if config is missing.

    sources_1090 = []
    if local_conf.get('dump1090'):
        sources_1090.append(local_conf['dump1090'])
    else:
        sources_1090 = [DEFAULT_PATHS['dump1090'], DEFAULT_URLS['dump1090']]

    sources_978 = []
    if local_conf.get('dump978'):
         sources_978.append(local_conf['dump978'])
    else:
         sources_978 = [DEFAULT_PATHS['dump978'], DEFAULT_URLS['dump978']]

    flights = []
    errors = []

    # Fetch 1090
    data_1090 = None
    used_source_1090 = None
    for src in sources_1090:
        data_1090 = fetch_json_from_path_or_url(src)
        if data_1090:
            used_source_1090 = src
            break

    if data_1090:
        now_ts = data_1090.get('now', time.time())
        for f in data_1090.get('aircraft', []):
            seen = f.get('seen', 999)
            if seen > 60: continue
            norm = normalize_local_flight(f, "Local (1090)")
            if norm:
                norm['timestamp'] = int(now_ts - seen)
                flights.append(norm)
    else:
        # Only log if we tried specific config and failed, or if neither default worked
        pass

    # Fetch 978
    data_978 = None
    for src in sources_978:
        data_978 = fetch_json_from_path_or_url(src)
        if data_978: break

    if data_978:
        now_ts = data_978.get('now', time.time())
        for f in data_978.get('aircraft', []):
            seen = f.get('seen', 999)
            if seen > 60: continue
            norm = normalize_local_flight(f, "Local (978)")
            if norm:
                norm['timestamp'] = int(now_ts - seen)
                flights.append(norm)

    return flights, []
