# Unified Flight Tracker
*A Professional Multi-Source Aviation Dashboard*

Unified Flight Tracker fuses real-time telemetry from FlightAware and Flightradar24 into a single, cohesive operational picture. It eliminates "ghost" aircraft through smart deconfliction algorithms and prioritizes the freshest data available.

---

## Features

- **Multi-Source Data Fusion**  
  Ingests and normalizes data from:
  - FlightAware AeroAPI v4  
  - Flightradar24 Commercial API  

- **Smart Deconfliction**  
  Merges duplicate aircraft using:
  - ICAO Hex codes  
  - Spatial matching with a 6 NM threshold  
  This ensures a clean map and prevents double-counted targets.

- **"Freshest Data" Priority**  
  Compares timestamps from each source and displays the most recent position report for each aircraft.

- **Tactical Dashboard**
  - **Left Panel:** Live, sortable flight table (Altitude, Speed, Heading, Distance).  
  - **Right Panel:** Full-screen Google Map with range rings and directional aircraft icons.

- **Observer-Centric Visualization**  
  Calculates real-time distance (NM) and bearing from your configured observer location to every aircraft.

---

## Installation Guide

Follow these steps to deploy the tracker on your local machine.

### 1. Prerequisites

Ensure you have Python 3.10+ installed:

    python --version

### 2. Initialize the Project

Create your project folder and set up a virtual environment to keep dependencies isolated:

    mkdir FlightTracker
    cd FlightTracker

    # Create Virtual Environment
    python -m venv venv

Activate the virtual environment:

**Mac/Linux:**

    source venv/bin/activate

**Windows (Command Prompt):**

    venv\Scripts\activate

### 3. Install Dependencies

Install the required Python packages:

    pip install flask requests pyyaml

Optionally, freeze dependencies:

    pip freeze > requirements.txt

---

## Configuration

The application uses a `config.yaml` file to manage API keys and your observer location.

Run the script once to auto-generate a default configuration:

    python flight_tracker.py

Then edit the generated `config.yaml` file:

    api_keys:
      # Leave default text if you do not have a specific key
      flightaware: "YOUR_FLIGHTAWARE_API_KEY"
      flightradar24: "YOUR_FR24_API_TOKEN"
      google_maps: "YOUR_GOOGLE_MAPS_API_KEY"

    observer:
      latitude: 39.8729      # Your Latitude
      longitude: -75.2437    # Your Longitude
      radius_nm: 50          # Range ring radius (nautical miles)

### How to Obtain API Keys

| Service        | Plan Required               | Where to Get It              |
|----------------|-----------------------------|------------------------------|
| FlightAware    | Personal / AeroAPI          | FlightAware Developer Portal |
| Flightradar24  | Commercial / Explorer       | FR24 API Portal              |
| Google Maps    | Standard (Free Tier)        | Google Cloud Console         |

Note: The Flightradar24 key required is for the **Commercial API**, not the personal feeder key. If you do not have a specific key, simply leave the default placeholder in `config.yaml` and the app will ignore that source.

---

## Usage

Once configured, start the server:

    python flight_tracker.py

Open your web browser and navigate to:

    http://localhost:5000

---

## Map Legend

The map uses color-coded symbols to indicate the source and status of each aircraft.

| Symbol | Color | Meaning                            |
|--------|--------|------------------------------------|
| House  | Green  | Observer Location (You)           |
| Circle | Red    | Range Limit (Defined in config)   |
| Plane  | Blue   | Data sourced uniquely from FlightAware |
| Plane  | Gold   | Data sourced uniquely from Flightradar24 |
| Plane  | Purple | Merged Target (Confirmed by both sources) |

---

## Repository Structure

    FlightTracker/
    │
    ├── flight_tracker.py      # Main application logic
    ├── README.md              # Documentation
    ├── .gitignore             # Git configuration
    │
    ├── config.yaml            # [IGNORED] Secrets & Config
    └── venv/                  # [IGNORED] Virtual Environment

---

## Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the project  
2. Create your feature branch:  
   
       git checkout -b feature/AmazingFeature

3. Commit your changes:  
   
       git commit -m "Add some AmazingFeature"

4. Push to the branch:  
   
       git push origin feature/AmazingFeature

5. Open a Pull Request

Built with Python and Flask.
