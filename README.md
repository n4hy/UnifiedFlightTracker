# Unified Flight Tracker

**A Professional Multi-Source Aviation Dashboard**

Unified Flight Tracker fuses real-time telemetry from **FlightAware** and **Flightradar24** into a single, cohesive operational picture. It eliminates "ghost" aircraft through smart deconfliction algorithms and prioritizes the freshest data available.

## Features

* **Multi-Source Data Fusion:** Ingests and normalizes data from FlightAware AeroAPI v4 and Flightradar24 Commercial API.
* **Smart Deconfliction:** Merges duplicate aircraft using ICAO Hex codes and spatial matching (6NM threshold) to ensure a clean map.
* **"Freshest Data" Priority:** Automatically compares timestamps to display the most recent position report from either source.
* **Tactical Dashboard:**
  * **Left Panel:** Live, sortable flight table (Altitude, Speed, Heading, Distance).
  * **Right Panel:** Full-screen Google Map with range rings and directional icons.
* **Observer Centric:** Calculates real-time distance from your specific location to every aircraft.

## Installation Guide

Follow these steps to deploy the tracker on your local machine.

### 1. Prerequisites

Ensure you have Python 3.10+ installed.

```bash
python --version
```

### 2. Initialize the Repository

Create your project folder and set up a virtual environment to keep dependencies clean.

```bash
# Create directory
mkdir FlightTracker
cd FlightTracker

# Create Virtual Environment
python -m venv venv

# Activate Environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages (flask, requests, pyyaml).

```bash
pip install flask requests pyyaml
```

## Configuration

The application uses a `config.yaml` file to manage API keys and your location.

1. Run the script once to auto-generate the file:

```bash
python flight_tracker.py
```

2. Edit the generated `config.yaml` file:

```yaml
api_keys:
  # Leave default text if you do not have a specific key
  flightaware: "YOUR_FLIGHTAWARE_API_KEY"
  flightradar24: "YOUR_FR24_API_TOKEN"
  google_maps: "YOUR_GOOGLE_MAPS_API_KEY"

observer:
  latitude: 39.8729    # Your Latitude
  longitude: -75.2437  # Your Longitude
  radius_nm: 50        # Range ring radius
```

### How to Obtain API Keys

| Service | Plan Required | Where to get it |
| :--- | :--- | :--- |
| **FlightAware** | Personal / AeroAPI | [Developer Portal](https://www.flightaware.com/aeroapi/portal) |
| **Flightradar24** | Commercial / Explorer | [FR24 API Portal](https://fr24api.flightradar24.com/) |
| **Google Maps** | Standard (Free Tier) | [Google Cloud Console](https://console.cloud.google.com/) |

> **Note:** The Flightradar24 key required is for the **Commercial API**, not the personal feeder key. If you do not have a specific key, simply leave the default placeholder in `config.yaml` and the app will ignore that source.

## Usage

Once configured, start the server:

```bash
python flight_tracker.py
```

Open your web browser and navigate to:

**http://localhost:5000**

## Map Legend

The map uses color-coded symbols to indicate the source and status of each aircraft.

| Symbol | Color | Meaning |
| :---: | :--- | :--- |
| House | **Green** | **Observer Location** (You) |
| Circle | **Red** | **Range Limit** (Defined in config) |
| Plane | **Blue** | Data sourced uniquely from **FlightAware** |
| Plane | **Gold** | Data sourced uniquely from **Flightradar24** |
| Plane | **Purple** | **Merged Target** (Confirmed by both sources) |

## Repository Structure

```text
FlightTracker/
│
├── flight_tracker.py      # Main application logic
├── README.md              # Documentation
├── .gitignore             # Git configuration
│
├── config.yaml            # [IGNORED] Secrets & Config
└── venv/                  # [IGNORED] Virtual Environment
```

## Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

_Built with Python and Flask_
