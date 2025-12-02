# Unified Flight Tracker

*A Professional Multi-Source Aviation Dashboard*

Unified Flight Tracker fuses real-time telemetry from FlightAware and Flightradar24 into a unified operational picture. It eliminates "ghost" aircraft via smart deconfliction algorithms and always displays the freshest available data.

---

## Features

- **Multi-Source Data Fusion** - Ingests and normalizes data from:
  - FlightAware AeroAPI v4
  - Flightradar24 Commercial API

- **Smart Deconfliction** - Merges duplicate aircraft based on:
  - ICAO Hex codes
  - Spatial matching within a 6 NM threshold
  - Ensures a clean, deduplicated aircraft map

- **Freshest Data Priority** - Automatically selects the most recent telemetry timestamp from either provider.

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
pip install flask requests pyyaml
```

Optional but recommended:

```bash
pip freeze > requirements.txt
```

---

## How to Deactivate the Virtual Environment

Return to your system Python environment:

```bash
deactivate
```

---

## Configuration

The application generates its configuration file on first run.

### 1. Auto-generate the config file

```bash
python flight_tracker.py
```

### 2. Edit the generated config.yaml

```yaml
api_keys:
  flightaware: "YOUR_FLIGHTAWARE_API_KEY"
  flightradar24: "YOUR_FR24_API_TOKEN"
  google_maps: "YOUR_GOOGLE_MAPS_API_KEY"

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
python flight_tracker.py
```

Open your browser:

```text
http://localhost:5000
```

---

## Map Legend

| Symbol | Color | Meaning |
|--------|-------|---------|
| House | Green | Your observer location |
| Circle | Red | Range boundary (from config) |
| Plane | Blue | FlightAware-only aircraft |
| Plane | Gold | Flightradar24-only aircraft |
| Plane | Purple | Merged aircraft (both sources) |

---

## Repository Structure

```text
FlightTracker/
├── flight_tracker.py      # Main application logic
├── README.md              # Documentation
├── .gitignore             # Git configuration
├── config.yaml            # [IGNORED] Secrets & Observer Config
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
