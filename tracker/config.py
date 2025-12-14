import os
import yaml
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

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
        "altitude_m": 0,
        "radius_nm": 50
    },
    "server": {
        "host": "0.0.0.0",
        "port": 5000
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
            logger.info(f"Created default configuration file at {CONFIG_FILE}")
            return DEFAULT_CONFIG
        except Exception as e:
            logger.error(f"Failed to create default config file: {e}")
            return DEFAULT_CONFIG

    # Check if file changed
    try:
        current_mtime = os.path.getmtime(CONFIG_FILE)
        if _cached_config and current_mtime == _cached_mtime:
            return _cached_config

        logger.info(f"Reloading configuration from {CONFIG_FILE}")
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)

            if not config:
                logger.warning(f"Configuration file {CONFIG_FILE} is empty.")
                if _cached_config:
                     logger.warning("Retaining previous valid configuration.")
                     return _cached_config
                logger.warning("Using default configuration.")
                return DEFAULT_CONFIG

            # Validate/Merge with defaults
            for section in DEFAULT_CONFIG:
                if section not in config:
                    config[section] = DEFAULT_CONFIG[section]

            _cached_config = config
            _cached_mtime = current_mtime
            logger.info("Configuration loaded successfully.")
            return config

    except yaml.YAMLError as e:
        logger.error(f"Error parsing {CONFIG_FILE}: {e}")
        if _cached_config:
            logger.warning("Retaining previous valid configuration due to parse error.")
            return _cached_config
        logger.warning("Reverting to default configuration due to parse error.")
        return DEFAULT_CONFIG

    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
        if _cached_config:
            return _cached_config
        return DEFAULT_CONFIG
