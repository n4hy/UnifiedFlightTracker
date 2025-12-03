from .geo import haversine_distance

def deconflict_data(fa_data, fr24_data, local_data=None):
    """
    Merges data prioritizing Local > ICAO Hex matching + Spatial backup.
    """
    SPATIAL_THRESHOLD_NM = 6.0
    if local_data is None: local_data = []

    merged_results = {}

    def clean_id(f): return str(f['hex_id']).strip().lower()

    # 1. Start with Local Data (Highest Priority)
    for f in local_data:
        # We track sources internally, but no longer store a set directly in the output dict
        # to avoid JSON serialization issues. We update 'source' string instead.
        merged_results[clean_id(f)] = f

    # Helper to merge into existing
    def merge_flight(f_new, source_label):
        f_id = clean_id(f_new)

        # Exact Match
        if f_id in merged_results:
            existing = merged_results[f_id]

            # Timestamp Logic: Keep Freshest Position
            ts_exist = existing.get('timestamp', 0)
            ts_new = f_new.get('timestamp', 0)

            if ts_new > ts_exist:
                # Update fields
                existing['lat'] = f_new['lat']
                existing['lon'] = f_new['lon']
                existing['heading'] = f_new['heading']
                existing['altitude'] = f_new['altitude']
                existing['speed'] = f_new['speed']
                existing['timestamp'] = ts_new

            # Update Source Label
            if "Local" in existing['source']:
                if source_label not in existing['source']:
                     existing['source'] = f"{existing['source']} + {source_label}"
            else:
                existing['source'] = "Merged"

            merged_results[f_id] = existing
            return True
        return False

    # 2. Process FlightAware
    unmerged_fa = []
    for f in fa_data:
        if not merge_flight(f, "FA"):
            unmerged_fa.append(f)

    # 3. Process FR24
    unmerged_fr24 = []
    for f in fr24_data:
        if not merge_flight(f, "FR24"):
            unmerged_fr24.append(f)

    # 4. Spatial Deconfliction
    def try_spatial_merge(candidate, source_label):
        best_match = None
        min_dist = float('inf')

        for m in merged_results.values():
            if m['lat'] and m['lon'] and candidate['lat'] and candidate['lon']:
                 dist = haversine_distance(m['lat'], m['lon'], candidate['lat'], candidate['lon'])
                 if dist < min_dist and dist <= SPATIAL_THRESHOLD_NM:
                     min_dist = dist
                     best_match = m

        if best_match:
            # Merge logic (same as exact match)
            ts_exist = best_match.get('timestamp', 0)
            ts_new = candidate.get('timestamp', 0)

            if ts_new > ts_exist:
                best_match['lat'] = candidate['lat']
                best_match['lon'] = candidate['lon']
                best_match['heading'] = candidate['heading']
                best_match['altitude'] = candidate['altitude']
                best_match['speed'] = candidate['speed']
                best_match['timestamp'] = ts_new

            if "Local" in best_match['source']:
                 if source_label not in best_match['source']:
                     best_match['source'] += f" + {source_label}"
            else:
                 best_match['source'] = "Merged"
            return True
        return False

    # Try spatial merge for FA
    final_fa = []
    for f in unmerged_fa:
        if not try_spatial_merge(f, "FA"):
            final_fa.append(f)

    # Add remaining FA to results
    for f in final_fa:
        merged_results[clean_id(f)] = f

    # Try spatial merge for FR24
    final_fr24 = []
    for f in unmerged_fr24:
        if not try_spatial_merge(f, "FR24"):
            final_fr24.append(f)

    # Add remaining FR24
    for f in final_fr24:
        merged_results[clean_id(f)] = f

    sorted_flights = sorted(list(merged_results.values()), key=lambda x: x['hex_id'])
    return sorted_flights
