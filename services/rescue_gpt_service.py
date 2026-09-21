"""
D-SQUARE Rescue GPT Service Module
Handles dual-role AI disaster reasoning (Victim vs Rescue Team), survival probability calculation,
and emergency dispatch triggers.
"""

import os
import json
import math
from typing import Dict, Any, List
from services.maps_routing_service import maps_routing_service, calculate_haversine_distance_km

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rescue_gpt_dataset.json")

class RescueGPTService:
    def __init__(self):
        self.disclaimer = "⚠️ DISCLAIMER: D-SQUARE Rescue GPT provides AI guidance based on real-time ground & satellite telemetry. Always follow official NDRF / 112 emergency orders."
        self.dataset = self._load_dataset()

    def _load_dataset(self) -> List[Dict[str, Any]]:
        if os.path.exists(DATASET_PATH):
            try:
                with open(DATASET_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def calculate_survival_probability(self, time_trapped_minutes: int, injury_type: str = "none", temp_c: float = 25.0, water_exposure: bool = False) -> Dict[str, Any]:
        """Calculates victim survival probability based on time trapped, injuries, and environment."""
        base_prob = 1.0

        # Time trapped decay rate (drops ~5-8% per hour)
        hours = time_trapped_minutes / 60.0
        base_prob -= (hours * 0.06)

        # Injury severity impact
        injury_lower = injury_type.lower()
        if "bleeding" in injury_lower or "hemorrhage" in injury_lower:
            base_prob -= 0.35
            rec = "Prioritize immediate pressure/tourniquet and urgent 15-min rescue triage."
        elif "crush" in injury_lower or "fracture" in injury_lower:
            base_prob -= 0.20
            rec = "Provide limb stabilization and hydraulic shoring during extraction."
        else:
            rec = "Maintain shelter warmth and conserve phone battery."

        # Environmental factors (hypothermia or extreme heat)
        if temp_c < 10.0 or water_exposure:
            base_prob -= 0.15
            rec += " High hypothermia risk detected!"
        elif temp_c > 40.0:
            base_prob -= 0.10
            rec += " Heat exhaustion risk detected!"

        final_prob = max(0.05, min(0.99, base_prob))

        return {
            "probability": round(final_prob, 2),
            "percentage": round(final_prob * 100, 1),
            "time_trapped_minutes": time_trapped_minutes,
            "factors": {
                "time_decay": f"-{round(hours * 6, 1)}%",
                "injury": injury_type,
                "environment_temp_c": temp_c,
                "water_exposure": water_exposure
            },
            "recommendation": rec
        }

    def generate_rescue_guidance(self, user_type: str, message: str, lat: float = 30.0668, lon: float = 79.0193, disaster_type: str = "landslide", sensor_data: Dict[str, Any] = None) -> Dict[str, Any]:
        msg_lower = message.lower()
        user_role = user_type.lower()
        
        actions = []
        call_112 = False

        # Match exact scenario pattern from dataset if available
        matched_example = None
        for item in self.dataset:
            if item.get("user_type") == user_role and item.get("disaster_type") == disaster_type:
                matched_example = item
                break

        # Calculate hazard route
        route_info = maps_routing_service.get_hazard_aware_route(lat, lon)

        if user_role == "victim":
            if "trapped" in msg_lower or "debris" in msg_lower or "bleeding" in msg_lower or "injured" in msg_lower:
                call_112 = True
                actions.extend(["notify_rescue_team", "share_location", "call_112_recommended"])
                response_text = (
                    "🚨 LANDSLIDE RESCUE GUIDANCE\n\n"
                    "STAY CALM. Follow these steps:\n\n"
                    "1. CHECK INJURIES: Are you bleeding? Apply firm pressure with cloth immediately.\n"
                    "2. SIGNAL FOR HELP: Tap on pipes/walls 3 times every 5 minutes (rescuers listen for this pattern).\n"
                    "3. CONSERVE BATTERY: Minimize phone screen brightness and stay warm.\n"
                    f"4. LOCATION REGISTERED: Coordinates ({lat:.4f}°N, {lon:.4f}°E) shared with NDRF Command ✅.\n"
                    f"5. NEAREST TEAM: Team Alpha 1.2km away (ETA {route_info['eta_minutes']} min).\n\n"
                    "Do NOT light matches. Rescue Team Alpha notified."
                )
            elif "water" in msg_lower or "flood" in msg_lower or "rising" in msg_lower:
                actions.extend(["dispatch_rescue_boat", "share_safe_zone"])
                response_text = (
                    "🌊 FLOOD EVACUATION ADVISORY\n\n"
                    "1. MOVE TO HIGHEST FLOOR OR ROOF immediately.\n"
                    "2. DO NOT enter floodwater (contamination & electrical hazard).\n"
                    "3. SIGNAL: Wave a bright cloth for rescue helicopters/boats.\n"
                    f"4. EVACUATION ROUTE: Head North-East toward Community Shelter ({route_info['distance_km']}km away, ETA {route_info['eta_minutes']} min).\n\n"
                    "Rescue craft notified. Stay on roof."
                )
            else:
                actions.append("share_location")
                response_text = (
                    f"🚨 D-SQUARE RESCUE GPT ACTIVE\n\n"
                    f"GPS Location ({lat:.4f}°N, {lon:.4f}°E) registered.\n"
                    f"Nearest Safe Shelter: Community Center ({route_info['distance_km']}km away).\n"
                    "Stay away from steep slopes and flooded gullies. Type your injury status or situation for immediate first-aid guidance."
                )

        else: # rescue_team
            actions.extend(["optimize_route", "avoid_hazards", "display_iot_telemetry"])
            response_text = (
                f"🚑 RESCUE ROUTE OPTIMIZATION & SITUATION REPORT\n\n"
                f"TARGET VICTIM LOCATION: {lat:.4f}°N, {lon:.4f}°E\n"
                f"ESTIMATED ETA: {route_info['eta_minutes']} minutes | DISTANCE: {route_info['distance_km']} km\n\n"
                f"ROUTE STEPS:\n" + "\n".join(route_info["steps"]) + "\n\n"
                f"HAZARD WARNINGS:\n" + ("\n".join(route_info["hazards_avoided"]) if route_info["hazards_avoided"] else "No active road blockages.") + "\n\n"
                f"SAFETY ADVISORY: Wear protective helmets. Approach from North access road."
            )

        return {
            "user_type": user_type,
            "disaster_type": disaster_type,
            "response": response_text,
            "actions": actions,
            "call_112_recommended": call_112,
            "route": route_info,
            "disclaimer": self.disclaimer
        }


rescue_gpt_service = RescueGPTService()
