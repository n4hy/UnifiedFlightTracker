# Unified Flight Tracker

*A Professional Multi-Source Aviation Dashboard*

Unified Flight Tracker fuses real-time telemetry from **local ADS-B receivers** (Piaware/Dump1090), FlightAware, and Flightradar24 into a unified operational picture. It eliminates "ghost" aircraft via smart deconfliction algorithms and prioritizes local data for the freshest possible tracking.

Code by Jules and me. 

---

## Features

- **Local Data Priority** - Directly ingests real-time data from your local Piaware/Dump1090 receiver.
  - Automatically detects local data via file path or HTTP.
  - Prioritizes local telemetry over API data to ensure zero latency.

- **Multi-Source Data Fusion** - Ingests and normalizes data from:
  - Local Dump1090 / Dump978
  - FlightAware AeroAPI v4
  - Flightradar24 Commercial API

- **Smart Deconfliction** - Merges duplicate aircraft based on:
  - Local vs Remote priority
  - ICAO Hex codes
  - Spatial matching within a 6 NM threshold
  - Ensures a clean, deduplicated aircraft map

- **Tactical Dashboard**
  - **Left Panel:** Sortable live flight table (Altitude, Speed, Heading, Distance)
  - **Right Panel:** Full-screen Google Map with range rings + directional aircraft icons

- **Observer-Centric Tracking** - Computes real-time bearing and distance (NM) from your configured observer location.

---

## Installation Guide

Follow these steps to deploy the tracker locally.

### 1. Prerequisites

Ensure Python 3.10+ is installed:

```bash
python --version
```

### 2. Initialize the Project Directory

```bash
mkdir FlightTracker
cd FlightTracker
```

### 3. Create and Activate Virtual Environment

```bash
python -m venv venv
```

**Activate (Mac/Linux):**

```bash
source venv/bin/activate
```

**Activate (Windows CMD):**

```bash
venv\Scripts\activate
```

**Activate (Windows PowerShell):**

```bash
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

The application generates its configuration file on first run.

### 1. Auto-generate the config file

```bash
python app.py
```

### 2. Edit the generated config.yaml

```yaml
api_keys:
  flightaware: "YOUR_FLIGHTAWARE_API_KEY"
  flightradar24: "YOUR_FR24_API_TOKEN"
  google_maps: "YOUR_GOOGLE_MAPS_API_KEY"

# Optional: Configure local data sources (Defaults shown below)
local_sources:
  dump1090: "http://localhost:8080/data/aircraft.json" # Or /run/dump1090-fa/aircraft.json
  dump978: "http://localhost:8978/data/aircraft.json"  # Or /run/dump978-fa/aircraft.json

observer:
  latitude: 39.8729      # Your latitude
  longitude: -75.2437    # Your longitude
  radius_nm: 50          # Range ring radius (nautical miles)
```

### How to Obtain API Keys

| Service | Plan Required | Where to Get It |
|---------|---------------|-----------------|
| FlightAware | Personal / AeroAPI | FlightAware Developer Portal |
| Flightradar24 | Commercial / Explorer Tier | FR24 API Portal |
| Google Maps | Standard (Free Tier) | Google Cloud Console |

> **Important:** FR24 requires a **Commercial API token**, not the feeder key. If you lack a token, the app simply ignores that provider.

---

## Usage

Start the local web server:

```bash
python app.py
```

Open your browser:

```text
http://localhost:5000
```

---

## Testing

To run the unit tests for the core logic and utilities:

```bash
python tests/test_logic.py
python tests/test_local.py
```

---

## Map Legend

| Symbol | Color | Meaning |
|--------|-------|---------|
| House | Green | Your observer location |
| Circle | Red | Range boundary (from config) |
| Plane | **Green** | **Local (Piaware/Dump1090) aircraft** |
| Plane | Purple | Merged aircraft (Local + Remote) |
| Plane | Blue | FlightAware-only aircraft |
| Plane | Gold | Flightradar24-only aircraft |

---

## Repository Structure

```text
FlightTracker/
├── app.py                 # Application entry point
├── config.yaml            # [IGNORED] Secrets & Observer Config
├── README.md              # Documentation
├── .gitignore             # Git configuration
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Frontend HTML/JS dashboard
├── tests/
│   ├── test_logic.py      # Core logic tests
│   └── test_local.py      # Local data parsing tests
├── tracker/               # Backend Package
│   ├── __init__.py
│   ├── api.py             # Remote API Ingestion
│   ├── config.py          # Configuration management
│   ├── core.py            # Deconfliction logic
│   ├── geo.py             # Geodesic math helpers
│   └── local.py           # Local Dump1090 Ingestion
└── venv/                  # [IGNORED] Python virtual environment
```

---

## Contributing

Contributions are welcome.

1. Fork the repository

2. Create a feature branch:

   ```bash
   git checkout -b feature/AmazingFeature
   ```

3. Commit your changes:

   ```bash
   git commit -m "Add AmazingFeature"
   ```

4. Push the branch:

   ```bash
   git push origin feature/AmazingFeature
   ```

5. Submit a Pull Request

---

Built with Python and Flask.
