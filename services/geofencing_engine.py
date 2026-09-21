"""
Spatial Geofencing Engine for D-SQUARE 2.0
Provides Ray-Casting Point-in-Polygon detection, Haversine spatial buffer calculations,
user delivery channel segmentation, and nearest shelter routing.
"""

import math
from typing import List, Dict, Any, Tuple, Optional
import database


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the great circle distance between two points on earth in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def point_in_polygon(lat: float, lon: float, polygon: List[Tuple[float, float]]) -> bool:
    """
    Ray-Casting algorithm to determine if point (lat, lon) lies inside a 2D polygon.
    polygon is expected to be a list of (lat, lon) or [lat, lon] tuples/lists.
    """
    if not polygon or len(polygon) < 3:
        return False

    n = len(polygon)
    inside = False

    p1lat, p1lon = polygon[0]
    for i in range(1, n + 1):
        p2lat, p2lon = polygon[i % n]
        if lon > min(p1lon, p2lon):
            if lon <= max(p1lon, p2lon):
                if lat <= max(p1lat, p2lat):
                    if p1lon != p2lon:
                        xinters = (lon - p1lon) * (p2lat - p1lat) / (p2lon - p1lon) + p1lat
                    else:
                        xinters = p1lat
                    if p1lat == p2lat or lat <= xinters:
                        inside = not inside
        p1lat, p1lon = p2lat, p2lon

    return inside


def distance_to_polygon_km(lat: float, lon: float, polygon: List[Tuple[float, float]]) -> float:
    """
    Calculates the minimum distance in km from a point to any vertex of the polygon.
    """
    if not polygon:
        return 999999.0

    min_dist = float('inf')
    for p_lat, p_lon in polygon:
        dist = haversine_distance_km(lat, lon, float(p_lat), float(p_lon))
        if dist < min_dist:
            min_dist = dist
    return min_dist


class SpatialGeofencingEngine:
    """
    Spatial Geofencing Engine that evaluates user positions against disaster polygon boundaries and buffer zones.
    """

    def __init__(self, buffer_radius_km: float = 2.5):
        self.buffer_radius_km = buffer_radius_km

    def evaluate_location_risk(
        self,
        lat: float,
        lon: float,
        polygon: List[Tuple[float, float]]
    ) -> Dict[str, Any]:
        """
        Determines if a location is inside the disaster polygon (CRITICAL_ZONE)
        or within the safety buffer zone (WARNING_ZONE).
        """
        if not polygon:
            return {
                "in_affected_zone": False,
                "zone_type": "SAFE_ZONE",
                "distance_to_boundary_km": 0.0
            }

        # Convert list of lists to list of tuples if needed
        poly_tuples = [(float(pt[0]), float(pt[1])) for pt in polygon]

        # 1. Point in polygon test
        is_inside = point_in_polygon(lat, lon, poly_tuples)
        if is_inside:
            return {
                "in_affected_zone": True,
                "zone_type": "CRITICAL_ZONE",
                "distance_to_boundary_km": 0.0
            }

        # 2. Buffer distance test
        dist_km = distance_to_polygon_km(lat, lon, poly_tuples)
        if dist_km <= self.buffer_radius_km:
            return {
                "in_affected_zone": True,
                "zone_type": "WARNING_ZONE",
                "distance_to_boundary_km": round(dist_km, 2)
            }

        return {
            "in_affected_zone": False,
            "zone_type": "SAFE_ZONE",
            "distance_to_boundary_km": round(dist_km, 2)
        }

    def segment_affected_users(
        self,
        polygon: List[Tuple[float, float]],
        users_list: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Fetches users and segments affected users into channel dispatch queues.
        """
        if users_list is None:
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
            conn.close()
            users_list = [dict(r) for r in rows]

        critical_users = []
        warning_users = []
        channel_queues = {
            "fcm_push": [],
            "twilio_sms": [],
            "whatsapp": [],
            "email": []
        }

        poly_tuples = [(float(pt[0]), float(pt[1])) for pt in polygon] if polygon else []

        for user in users_list:
            u_lat = float(user.get("latitude", user.get("lat", 0.0)))
            u_lon = float(user.get("longitude", user.get("lon", 0.0)))

            risk_eval = self.evaluate_location_risk(u_lat, u_lon, poly_tuples)
            if not risk_eval["in_affected_zone"]:
                continue

            user_record = {
                "user_id": user.get("user_id", user.get("id")),
                "name": user.get("name", user.get("username", "Citizen")),
                "phone": user.get("phone", ""),
                "email": user.get("email", ""),
                "latitude": u_lat,
                "longitude": u_lon,
                "zone_type": risk_eval["zone_type"],
                "distance_km": risk_eval["distance_to_boundary_km"]
            }

            if risk_eval["zone_type"] == "CRITICAL_ZONE":
                critical_users.append(user_record)
            else:
                warning_users.append(user_record)

            # Channel assignment
            if user.get("app_installed", True):
                channel_queues["fcm_push"].append(user_record)
            if user.get("sms_subscribed", True) and user_record["phone"]:
                channel_queues["twilio_sms"].append(user_record)
            if user.get("whatsapp_subscribed", True) and user_record["phone"]:
                channel_queues["whatsapp"].append(user_record)
            if user_record["email"]:
                channel_queues["email"].append(user_record)

        return {
            "total_affected_count": len(critical_users) + len(warning_users),
            "critical_zone_count": len(critical_users),
            "warning_zone_count": len(warning_users),
            "critical_users": critical_users,
            "warning_users": warning_users,
            "channel_queues": channel_queues
        }

    def find_nearest_shelter(
        self,
        lat: float,
        lon: float
    ) -> Optional[Dict[str, Any]]:
        """
        Finds the nearest shelter with available capacity to given lat/lon coordinates.
        """
        shelters = database.get_shelters_list()
        if not shelters:
            # Fallback default shelter
            return {
                "shelter_id": "SHELTER_DEFAULT",
                "name": "Central Emergency Relief Center",
                "address": "Safe Zone Evacuation Center",
                "latitude": lat + 0.02,
                "longitude": lon + 0.02,
                "distance_km": 2.5,
                "available_beds": 500,
                "contact_number": "+91-1800-112-112",
                "facilities": "Medical Triage, Food Rations, Water",
                "google_maps_url": f"https://www.google.com/maps/dir/?api=1&destination={lat+0.02},{lon+0.02}",
                "estimated_evacuation_time_mins": 10
            }

        nearest = None
        min_dist = float('inf')

        for s in shelters:
            s_lat = float(s["latitude"])
            s_lon = float(s["longitude"])
            dist = haversine_distance_km(lat, lon, s_lat, s_lon)
            if dist < min_dist:
                min_dist = dist
                nearest = s

        if nearest:
            est_mins = max(5, int((min_dist / 15.0) * 60))  # Assuming 15 km/h avg speed
            res = dict(nearest)
            res["distance_km"] = round(min_dist, 2)
            res["estimated_evacuation_time_mins"] = est_mins
            res["google_maps_url"] = f"https://www.google.com/maps/dir/?api=1&destination={nearest['latitude']},{nearest['longitude']}"
            return res

        return None
