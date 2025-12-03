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
