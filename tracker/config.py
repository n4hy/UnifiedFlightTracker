import os
import sys

try:
    import yaml
except ImportError:
    print("Error: PyYAML is missing. Please run: pip install -r requirements.txt")
    sys.exit(1)

CONFIG_FILE = 'config.yaml'

DEFAULT_CONFIG = {
    "api_keys": {
        "flightaware": "YOUR_FLIGHTAWARE_API_KEY",
        "flightradar24": "YOUR_FR24_API_TOKEN",
        "google_maps": "YOUR_GOOGLE_MAPS_API_KEY"
    },
    "local_sources": {
        "dump1090": "/run/dump1090-fa/aircraft.json",
        "dump978": "/run/dump978-fa/aircraft.json"
    },
    "observer": {
        "latitude": 39.0,
        "longitude": -75.0,
        "radius_nm": 50
    },
    "server": {
        "host": "0.0.0.0",
        "port": 5000
    },
    "api_caching": {
        "ttl_seconds": 60
    }
}

# Simple cache to avoid re-reading file on every request
_cached_config = None
_cached_mtime = 0

def load_config():
    global _cached_config, _cached_mtime

    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'w') as f:
                yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
            _cached_config = DEFAULT_CONFIG
            _cached_mtime = os.path.getmtime(CONFIG_FILE)
            return DEFAULT_CONFIG
        except Exception as e:
            return DEFAULT_CONFIG

    # Check if file changed
    try:
        current_mtime = os.path.getmtime(CONFIG_FILE)
        if _cached_config and current_mtime == _cached_mtime:
            return _cached_config

        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
            if not config: return DEFAULT_CONFIG
            for section in DEFAULT_CONFIG:
                if section not in config:
                    config[section] = DEFAULT_CONFIG[section]

            _cached_config = config
            _cached_mtime = current_mtime
            return config
    except Exception as e:
        return DEFAULT_CONFIG
