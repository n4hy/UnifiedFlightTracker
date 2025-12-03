import unittest
import math
import sys
import os

# Add parent dir to path to import tracker
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tracker.geo import haversine_distance, get_bounding_box
from tracker.core import deconflict_data
from tracker.api import parse_fa_time

class TestFlightTracker(unittest.TestCase):

    def test_haversine_distance(self):
        # Test case: Distance between JFK and LHR (approx)
        # JFK: 40.6413, -73.7781
        # LHR: 51.4700, -0.4543
        # Expected distance is roughly 2996 NM
        lat1, lon1 = 40.6413, -73.7781
        lat2, lon2 = 51.4700, -0.4543
        dist = haversine_distance(lat1, lon1, lat2, lon2)
        self.assertTrue(2990 < dist < 3010, f"Distance {dist} not within expected range")

        # Zero distance
        self.assertEqual(haversine_distance(0, 0, 0, 0), 0)

    def test_get_bounding_box(self):
        lat, lon = 40.0, -75.0
        radius = 60 # 1 degree is roughly 60NM
        min_lat, max_lat, min_lon, max_lon = get_bounding_box(lat, lon, radius)

        # Latitude should be +/- 1 degree approx
        self.assertAlmostEqual(min_lat, 39.0, delta=0.1)
        self.assertAlmostEqual(max_lat, 41.0, delta=0.1)

        # Longitude varies by cos(lat)
        # 1 deg lon at 40 lat = 60 * cos(40) = 46 NM
        # So 60 NM is > 1 deg lon
        self.assertTrue(max_lon > -74.0)
        self.assertTrue(min_lon < -76.0)

    def test_deconflict_data_merge(self):
        # Setup: One FA flight and one FR24 flight that are the same aircraft
        fa_data = [{
            "source": "FlightAware",
            "hex_id": "ABCDEF",
            "callsign": "TEST01",
            "lat": 40.0,
            "lon": -74.0,
            "heading": 100,
            "altitude": 10000,
            "speed": 250,
            "type": "B737",
            "timestamp": 1000
        }]

        fr24_data = [{
            "source": "Flightradar24",
            "hex_id": "abcdef", # Lowercase to test normalization
            "callsign": "TEST01",
            "lat": 40.001, # Slightly different position
            "lon": -74.001,
            "heading": 100,
            "altitude": 10000,
            "speed": 250,
            "type": "B737",
            "timestamp": 1005 # Newer
        }]

        merged = deconflict_data(fa_data, fr24_data)
        self.assertEqual(len(merged), 1)
        flight = merged[0]
        self.assertEqual(flight['hex_id'].lower(), 'abcdef')

        # Check if it picked the newer data (FR24)
        self.assertEqual(flight['timestamp'], 1005)
        self.assertEqual(flight['lat'], 40.001)
        self.assertTrue(flight['_merged'])

    def test_deconflict_data_spatial(self):
        # Setup: Different Hex IDs but close spatially
        fa_data = [{
            "source": "FlightAware",
            "hex_id": "AAAAAA",
            "callsign": "TEST01",
            "lat": 40.0,
            "lon": -74.0,
            "heading": 100,
            "altitude": 10000,
            "speed": 250,
            "type": "B737",
            "timestamp": 1000
        }]

        fr24_data = [{
            "source": "Flightradar24",
            "hex_id": "BBBBBB",
            "callsign": "TEST01",
            "lat": 40.01, # Close enough (approx 0.6 NM away)
            "lon": -74.01,
            "heading": 100,
            "altitude": 10000,
            "speed": 250,
            "type": "B737",
            "timestamp": 1005
        }]

        merged = deconflict_data(fa_data, fr24_data)
        self.assertEqual(len(merged), 1)
        flight = merged[0]
        # Should be merged
        self.assertTrue(flight.get('_merged'))

    def test_deconflict_data_distinct(self):
        # Setup: Different Hex IDs and far apart
        fa_data = [{
            "source": "FlightAware",
            "hex_id": "AAAAAA",
            "callsign": "TEST01",
            "lat": 40.0,
            "lon": -74.0,
            "heading": 100,
            "altitude": 10000,
            "speed": 250,
            "type": "B737",
            "timestamp": 1000
        }]

        fr24_data = [{
            "source": "Flightradar24",
            "hex_id": "BBBBBB",
            "callsign": "TEST02",
            "lat": 41.0, # Far away (60 NM)
            "lon": -75.0,
            "heading": 100,
            "altitude": 10000,
            "speed": 250,
            "type": "B737",
            "timestamp": 1005
        }]

        merged = deconflict_data(fa_data, fr24_data)
        self.assertEqual(len(merged), 2)

    def test_parse_fa_time(self):
        ts = parse_fa_time("2023-01-01T12:00:00Z")
        self.assertTrue(ts > 0)

if __name__ == '__main__':
    unittest.main()
