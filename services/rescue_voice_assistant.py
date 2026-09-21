"""
Disaster Rescue AI & Voice Assistant Service
Provides voice-guided turn-by-turn evacuation instructions and tracks rescue team locations.
"""

from typing import Dict, Any, List
from services.safe_zone_service import calculate_haversine_distance_km

class RescueVoiceAssistant:
    def __init__(self):
        self.active_teams = [
            {"team_id": "RESCUE_ALPHA_01", "name": "NDRF Quick Response Team 1", "lat": 30.0750, "lon": 79.0250, "status": "DISPATCHED", "eta_minutes": 12},
            {"team_id": "RESCUE_BRAVO_02", "name": "SDRF Mountain Evacuation Unit", "lat": 30.0510, "lon": 79.0110, "status": "STANDBY", "eta_minutes": 25}
        ]

    def get_evacuation_route(self, start_lat: float, start_lon: float, lang: str = "en") -> Dict[str, Any]:
        target_lat = 30.0820
        target_lon = 79.0310
        dist = calculate_haversine_distance_km(start_lat, start_lon, target_lat, target_lon)

        if lang == "hi":
            instructions = [
                "1. मंदिर के पास बाएं मुड़ें और उत्तर दिशा में 200 मीटर चलें।",
                "2. भूस्खलन क्षेत्र से दूर मुख्य पक्की सड़क का पालन करें।",
                "3. 500 मीटर सीधे जिला हाई स्कूल राहत केंद्र की ओर बढ़ें।"
            ]
            voice_summary = f"सुरक्षित क्षेत्र 500 मीटर की दूरी पर है। मुख्य सड़क का पालन करें।"
        else:
            instructions = [
                "1. Turn left near the temple and proceed 200m North.",
                "2. Follow the paved main road away from the slope hazard area.",
                "3. Continue 500m directly to District High School Relief Center."
            ]
            voice_summary = "Safe relief center is 500 meters ahead on the main road. Evacuate now."

        return {
            "start_coordinates": {"lat": start_lat, "lon": start_lon},
            "destination_name": "District High School Relief Center",
            "destination_coordinates": {"lat": target_lat, "lon": target_lon},
            "distance_km": round(dist, 2),
            "estimated_walk_minutes": max(5, int(dist * 12)),
            "instructions": instructions,
            "voice_summary": voice_summary,
            "language": lang
        }

    def get_active_rescue_teams(self) -> List[Dict[str, Any]]:
        return self.active_teams


rescue_voice_assistant = RescueVoiceAssistant()
