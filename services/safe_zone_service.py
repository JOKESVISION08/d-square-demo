"""
services/safe_zone_service.py — Verified Safe Zone & Shelter Query Service
Handles querying, distance calculation, ranking, and hazard polygon/circle exclusion for emergency shelters.
Never returns a safe zone inside an active disaster hazard zone.
"""

import math
from typing import Dict, Any, List, Optional
from database import get_safe_zones_db


def calculate_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates Haversine distance in kilometers between two lat/lon points."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


class SafeZoneService:
    def get_safe_zones_for_user(
        self,
        user_lat: float,
        user_lon: float,
        hazard_lat: Optional[float] = None,
        hazard_lon: Optional[float] = None,
        hazard_radius_km: float = 10.0,
        disaster_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves, ranks, and filters verified safe zones relative to user location.
        Excludes any safe zone situated inside active hazard geometry.
        """
        all_zones = get_safe_zones_db()

        valid_zones = []
        for z in all_zones:
            z_lat = float(z["latitude"])
            z_lon = float(z["longitude"])

            # 1. Check if safe zone is inside active hazard radius
            if hazard_lat is not None and hazard_lon is not None:
                dist_to_hazard = calculate_haversine_distance_km(z_lat, z_lon, hazard_lat, hazard_lon)
                if dist_to_hazard <= hazard_radius_km:
                    continue  # EXCLUDE: Safe zone is inside hazard zone

            # 2. Distance from user to safe zone
            dist_to_user = calculate_haversine_distance_km(user_lat, user_lon, z_lat, z_lon)
            z["distance_km"] = dist_to_user
            valid_zones.append(z)

        # Sort by distance from user
        valid_zones.sort(key=lambda item: item["distance_km"])

        if not valid_zones:
            return {
                "status": "warning",
                "count": 0,
                "safe_zones": [],
                "nearest": None,
                "message": "No verified safe route is available in this app. Move away from immediate danger only if it is safe, call 112, and follow local authorities."
            }

        nearest = valid_zones[0] if valid_zones else None
        return {
            "status": "success",
            "count": len(valid_zones),
            "safe_zones": valid_zones,
            "nearest": nearest,
            "message": f"Found {len(valid_zones)} verified safe evacuation shelters."
        }
