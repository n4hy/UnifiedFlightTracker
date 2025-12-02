Unified Flight TrackerA Professional Multi-Source Aviation DashboardUnified Flight Tracker fuses real-time telemetry from FlightAware and Flightradar24 into a single, cohesive operational picture. It eliminates "ghost" aircraft through smart deconfliction algorithms and prioritizes the freshest data available.FeaturesMulti-Source Data Fusion: Ingests and normalizes data from FlightAware AeroAPI v4 and Flightradar24 Commercial API.Smart Deconfliction: Merges duplicate aircraft using ICAO Hex codes and spatial matching (6NM threshold) to ensure a clean map."Freshest Data" Priority: Automatically compares timestamps to display the most recent position report from either source.Tactical Dashboard:Left Panel: Live, sortable flight table (Altitude, Speed, Heading, Distance).Right Panel: Full-screen Google Map with range rings and directional icons.Observer Centric: Calculates real-time distance from your specific location to every aircraft.Installation GuideFollow these steps to deploy the tracker on your local machine.1. PrerequisitesEnsure you have Python 3.10+ installed.python --version
2. Initialize the RepositoryCreate your project folder and set up a virtual environment to keep dependencies clean.# Create directory
mkdir FlightTracker
cd FlightTracker

# Create Virtual Environment
python -m venv venv

# Activate Environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
3. Install DependenciesInstall the required Python packages (flask, requests, pyyaml).pip install flask requests pyyaml
ConfigurationThe application uses a config.yaml file to manage API keys and your location.Run the script once to auto-generate the file:python flight_tracker.py
Edit the generated config.yaml file:api_keys:
  # Leave default text if you do not have a specific key
  flightaware: "YOUR_FLIGHTAWARE_API_KEY"
  flightradar24: "YOUR_FR24_API_TOKEN"
  google_maps: "YOUR_GOOGLE_MAPS_API_KEY"

observer:
  latitude: 39.8729    # Your Latitude
  longitude: -75.2437  # Your Longitude
  radius_nm: 50        # Range ring radius
How to Obtain API KeysServicePlan RequiredWhere to get itFlightAwarePersonal / AeroAPIDeveloper PortalFlightradar24Commercial / ExplorerFR24 API PortalGoogle MapsStandard (Free Tier)Google Cloud ConsoleNote: The Flightradar24 key required is for the Commercial API, not the personal feeder key. If you do not have a specific key, simply leave the default placeholder in config.yaml and the app will ignore that source.UsageOnce configured, start the server:python flight_tracker.py
Open your web browser and navigate to:http://localhost:5000Map LegendThe map uses color-coded symbols to indicate the source and status of each aircraft.SymbolColorMeaningHouseGreenObserver Location (You)CircleRedRange Limit (Defined in config)PlaneBlueData sourced uniquely from FlightAwarePlaneGoldData sourced uniquely from Flightradar24PlanePurpleMerged Target (Confirmed by both sources)Repository StructureFlightTracker/
│
├── flight_tracker.py      # Main application logic
├── README.md              # Documentation
├── .gitignore             # Git configuration
│
├── config.yaml            # [IGNORED] Secrets & Config
└── venv/                  # [IGNORED] Virtual Environment
ContributingContributions, issues, and feature requests are welcome!Fork the ProjectCreate your Feature Branch (git checkout -b feature/AmazingFeature)Commit your Changes (git commit -m 'Add some AmazingFeature')Push to the Branch (git push origin feature/AmazingFeature)Open a Pull RequestBuilt with Python and Flask
