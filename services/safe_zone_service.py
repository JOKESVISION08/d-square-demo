"""
Safe Zone Service Module
Calculates nearest safe shelters and Haversine distances.
"""

import math
from typing import List, Dict, Any

def calculate_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

class SafeZoneService:
    def get_safe_zones(self, user_lat: float = 30.0668, user_lon: float = 79.0193) -> List[Dict[str, Any]]:
        zones = [
            {"name": "District High School Relief Center", "lat": 30.0820, "lon": 79.0310, "type": "High Ground School"},
            {"name": "Govt Sports Complex Shelter", "lat": 30.0550, "lon": 79.0050, "type": "Indoor Stadium"}
        ]
        for z in zones:
            z["distance_km"] = round(calculate_haversine_distance_km(user_lat, user_lon, z["lat"], z["lon"]), 2)
        return sorted(zones, key=lambda x: x["distance_km"])
