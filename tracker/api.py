import requests
import time
import logging
from datetime import datetime, timezone
from .geo import get_bounding_box
from .config import load_config

logger = logging.getLogger(__name__)

# Global In-Memory Cache
# Structure: { "key": (timestamp, data, errors) }
_api_cache = {}

def get_cached_response(key, ttl):
    """Returns cached data if valid, else None."""
    if key in _api_cache:
        timestamp, data, errors = _api_cache[key]
        if time.time() - timestamp < ttl:
            logger.debug(f"Cache Hit for {key}")
            return data, errors
    return None

def set_cached_response(key, data, errors):
    """Stores data in cache."""
    # Prevent unbounded growth: If cache is too big, clear it.
    if len(_api_cache) > 100:
        _api_cache.clear()
        logger.info("Cache cleared due to size limit.")

    _api_cache[key] = (time.time(), data, errors)

def parse_fa_time(iso_str):
    try:
        # Handle fractional seconds if present by taking only first 19 chars (YYYY-MM-DDTHH:MM:SS)
        # or robustly parsing ISO format
        # If iso_str has fractional seconds e.g. .123456Z, strptime %Z might fail or we need specific format
        # Simplified approach:
        if '.' in iso_str:
            iso_str = iso_str.split('.')[0] + 'Z'

        dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception as e:
        logger.warning(f"Failed to parse FlightAware time {iso_str}: {e}")
        return int(time.time())

def fetch_flightaware(lat, lon, radius_nm):
    config = load_config()

    # Check Cache
    ttl = config.get('api_caching', {}).get('ttl_seconds', 60)
    cache_key = f"fa_{lat}_{lon}_{radius_nm}"
    cached = get_cached_response(cache_key, ttl)
    if cached:
        return cached

    api_key = config['api_keys'].get('flightaware')

    # If key is None (commented out), empty, or default, return empty list cleanly.
    if not api_key or str(api_key).strip() == "" or "YOUR_" in str(api_key):
        return [], [] # Return no flights and NO errors - silent disable

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

        set_cached_response(cache_key, normalized_flights, [])
        return normalized_flights, []

    except requests.exceptions.RequestException as e:
        logger.error(f"FlightAware API Error: {e}")
        msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
             if e.response.status_code == 400:
                 msg = "400 - Bad Request (Check Query Syntax)"
             else:
                 msg = f"{e.response.status_code} - {e.response.reason}"

        errors = [f"FlightAware Error: {msg}"]
        # We generally don't cache errors for full duration, but we could for a short time.
        # For simplicity, let's not cache errors so retries happen.
        return [], errors
    except Exception as e:
        logger.error(f"Unexpected FlightAware Error: {e}")
        return [], [f"FlightAware Error: {str(e)}"]

def fetch_flightradar24(lat, lon, radius_nm):
    config = load_config()

    # Check Cache
    ttl = config.get('api_caching', {}).get('ttl_seconds', 60)
    cache_key = f"fr24_{lat}_{lon}_{radius_nm}"
    cached = get_cached_response(cache_key, ttl)
    if cached:
        return cached

    token = config['api_keys'].get('flightradar24')

    # If token is None (commented out), empty, or default, return empty list cleanly.
    if not token or str(token).strip() == "" or "YOUR_" in str(token):
        return [], [] # Return no flights and NO errors - silent disable

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

        set_cached_response(cache_key, normalized_flights, [])
        return normalized_flights, []

    except requests.exceptions.RequestException as e:
        logger.error(f"FR24 API Error: {e}")
        msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
             msg = f"{e.response.status_code} - {e.response.text}"
        return [], [f"FR24 Error: {msg}"]
    except Exception as e:
        logger.error(f"Unexpected FR24 Error: {e}")
        return [], [f"FR24 Error: {str(e)}"]
