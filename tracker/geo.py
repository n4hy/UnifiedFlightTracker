import math

def get_bounding_box(lat, lon, radius_nm):
    R = 3440.065
    max_lat = lat + math.degrees(radius_nm / R)
    min_lat = lat - math.degrees(radius_nm / R)
    max_lon = lon + math.degrees(radius_nm / R / math.cos(math.radians(lat)))
    min_lon = lon - math.degrees(radius_nm / R / math.cos(math.radians(lat)))
    return round(min_lat, 4), round(max_lat, 4), round(min_lon, 4), round(max_lon, 4)

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 3440.065
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calculate_az_el(obs_lat, obs_lon, obs_alt_m, target_lat, target_lon, target_alt_m):
    """
    Calculates the Azimuth (degrees) and Elevation (degrees) of a target
    relative to an observer using a spherical earth model.
    """
    R_EARTH = 6371000.0 # meters

    lat1_rad = math.radians(obs_lat)
    lon1_rad = math.radians(obs_lon)
    lat2_rad = math.radians(target_lat)
    lon2_rad = math.radians(target_lon)

    d_lon = lon2_rad - lon1_rad

    # Azimuth Calculation (Bearing)
    y = math.sin(d_lon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(d_lon)
    azimuth_rad = math.atan2(y, x)
    azimuth_deg = (math.degrees(azimuth_rad) + 360) % 360

    # Elevation Calculation

    # Central angle (gamma) between the two points on the sphere
    sin_dlat_2 = math.sin((lat2_rad - lat1_rad) / 2)**2
    sin_dlon_2 = math.sin(d_lon / 2)**2
    a = sin_dlat_2 + math.cos(lat1_rad) * math.cos(lat2_rad) * sin_dlon_2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distances from Earth center
    r_obs = R_EARTH + obs_alt_m
    r_target = R_EARTH + target_alt_m

    # Slant Range (s) via Law of Cosines
    s_sq = r_obs**2 + r_target**2 - 2 * r_obs * r_target * math.cos(c)

    # Handle coincident points
    if s_sq <= 0.0001:
        if r_target > r_obs: return 0.0, 90.0 # Directly above
        elif r_target < r_obs: return 0.0, -90.0 # Directly below
        else: return 0.0, 0.0 # Same point

    s = math.sqrt(s_sq)

    # Zenith Angle (phi) via Law of Cosines
    # The triangle is Center-Observer-Target.
    # The angle calculated directly by Law of Cosines using r_t opposite is the angle at O between OC (Down) and OT.
    # We want the angle between CO (Up) and OT.
    # cos(angle_internal) = (r_obs^2 + s^2 - r_target^2) / (2 * r_obs * s)
    # cos(zenith) = -cos(angle_internal) = (r_target^2 - r_obs^2 - s_sq) / (2 * r_obs * s)

    cos_phi = (r_target**2 - r_obs**2 - s_sq) / (2 * r_obs * s)

    # Clamp value to [-1, 1] to avoid domain errors
    cos_phi = max(-1.0, min(1.0, cos_phi))

    phi = math.acos(cos_phi)
    elevation_deg = 90.0 - math.degrees(phi)

    return round(azimuth_deg, 1), round(elevation_deg, 1)
