from .geo import haversine_distance

def deconflict_data(fa_data, fr24_data):
    """
    Merges data prioritizing ICAO Hex matching + Spatial backup.
    """
    SPATIAL_THRESHOLD_NM = 6.0

    merged_results = {}

    # Index FA Data
    fa_indexed = {}
    def clean_id(f): return str(f['hex_id']).strip().lower()

    for f in fa_data:
        f['_merged'] = False
        fa_indexed[clean_id(f)] = f

    for fr in fr24_data:
        fr_id = clean_id(fr)
        match_found = False
        fa_match = None

        # 1. Exact ICAO Match
        if fr_id in fa_indexed:
            fa_match = fa_indexed[fr_id]
            match_found = True
        else:
            # 2. Spatial Match (if ICAO mismatch)
            closest_dist = float('inf')
            for fa_id, fa in fa_indexed.items():
                if fa.get('_merged'): continue
                if fa['lat'] and fa['lon'] and fr['lat'] and fr['lon']:
                    dist = haversine_distance(fa['lat'], fa['lon'], fr['lat'], fr['lon'])
                    if dist < closest_dist and dist <= SPATIAL_THRESHOLD_NM:
                        closest_dist = dist
                        fa_match = fa
                        match_found = True

        if match_found and fa_match:
            # Timestamp Logic: Keep Freshest Position
            fa_ts = fa_match.get('timestamp', 0)
            fr_ts = fr.get('timestamp', 0)

            fa_match['_merged'] = True
            fa_match['source'] = "Merged (FA+FR24)"

            if fr_ts >= fa_ts:
                fa_match['lat'] = fr['lat']
                fa_match['lon'] = fr['lon']
                fa_match['heading'] = fr['heading']
                fa_match['altitude'] = fr['altitude']
                fa_match['speed'] = fr['speed']
                fa_match['timestamp'] = fr['timestamp']

            merged_results[clean_id(fa_match)] = fa_match
        else:
            merged_results[fr_id] = fr

    for fa in fa_indexed.values():
        if not fa.get('_merged'):
            merged_results[clean_id(fa)] = fa

    # Sort results by Hex ID by default
    sorted_flights = sorted(list(merged_results.values()), key=lambda x: x['hex_id'])
    return sorted_flights
