import unittest
import math
from tracker.geo import calculate_az_el

class TestGeoCalc(unittest.TestCase):

    def test_az_el_same_location_different_altitude(self):
        # Directly overhead
        az, el = calculate_az_el(0, 0, 0, 0, 0, 1000)
        self.assertEqual(el, 90.0)

        # Directly below (underground?)
        az, el = calculate_az_el(0, 0, 1000, 0, 0, 0)
        self.assertEqual(el, -90.0)

    def test_az_el_north(self):
        # Target due North
        # 1 deg lat is approx 111km.
        # Flat earth approx: atan(10km alt / 111km dist) ~= small angle
        # But using spherical calc.

        # Obs: 0,0,0
        # Target: 1,0,0 (1 degree north)
        az, el = calculate_az_el(0, 0, 0, 1, 0, 0)
        self.assertAlmostEqual(az, 0.0, delta=0.1)
        # Elevation should be slightly below 0 due to earth curvature if at same altitude (0)
        self.assertTrue(el < 0)

    def test_az_el_east(self):
        # Target due East
        az, el = calculate_az_el(0, 0, 0, 0, 1, 0)
        self.assertAlmostEqual(az, 90.0, delta=0.1)

    def test_az_el_known_case(self):
        # Manual check or approximate check
        # Obs at sea level. Target 100km away, 10km up.
        # 100km is approx 0.9 degrees.

        # Let's try: Obs (0,0,0). Target (0.9, 0, 10000).
        # Slant range roughly sqrt(100^2 + 10^2) ~ 100.5km
        # Flat earth angle = atan(10/100) = 5.7 degrees.
        # Due to curvature, target drops. Curvature drop for 100km is h = d^2 / 2R = 100^2 / 12740 ~ 0.78km.
        # So effective height relative to horizon tangent is 10 - 0.78 = 9.22km.
        # Angle ~ atan(9.22/100) ~ 5.2 degrees.

        az, el = calculate_az_el(0, 0, 0, 0.9, 0, 10000)
        self.assertAlmostEqual(az, 0.0, delta=0.1)
        self.assertTrue(4.5 < el < 6.5)

    def test_az_el_horizon(self):
        # Determine geometric horizon distance for observer at 1000m.
        # d ~ 3.57 * sqrt(h_meters) (result in km) -> 3.57 * sqrt(1000) ~ 112km.
        # At this distance, elevation should be 0.

        # 112km is approx 1 degree.
        # Obs: 0,0, 1000m. Target: 1.0, 0, 0m.
        az, el = calculate_az_el(0, 0, 1000, 1.0, 0, 0)
        self.assertAlmostEqual(az, 0.0, delta=0.1)
        self.assertAlmostEqual(el, 0.0, delta=1.0) # Approx check

if __name__ == '__main__':
    unittest.main()
