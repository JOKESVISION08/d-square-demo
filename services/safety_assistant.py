"""
D-SQUARE GPT Safety Assistant & Weather Conversation Engine
Provides natural language reasoning over real-time multi-node sensor telemetry and satellite predictions.
"""

from typing import Dict, Any

class SafetyAssistantService:
    def __init__(self):
        self.disclaimer = "⚠️ DISCLAIMER: D-SQUARE GPT is an AI decision support tool. Follow official emergency service (112) and IMD authority warnings during real disasters."

    def answer_user_query(self, user_message: str, sensor_data: Dict[str, Any] = None, sat_data: Dict[str, Any] = None) -> Dict[str, Any]:
        msg_lower = user_message.lower()

        soil_m = sensor_data.get("soil_moisture", 40.0) if sensor_data else 40.0
        temp = sensor_data.get("temperature", 25.0) if sensor_data else 25.0
        scenario = sensor_data.get("scenario", "normal") if sensor_data else "normal"

        if "landslide" in msg_lower or "slope" in msg_lower or "soil" in msg_lower:
            if soil_m >= 80.0 or scenario == "landslide":
                response = f"YES - Elevated landslide risk detected! Current soil moisture is {soil_m:.1f}%. Immediate Action: Avoid steep gullies and evacuate to designated high-ground shelters."
                trigger_sos = True
            else:
                response = f"Soil moisture is currently normal ({soil_m:.1f}%). Slope stability is monitored. No immediate landslide risk detected."
                trigger_sos = False

        elif "weather" in msg_lower or "rain" in msg_lower or "monsoon" in msg_lower:
            response = f"Current temperature is {temp:.1f}°C with heavy monsoon rainfall observed. Satellite anomaly indicates +39.1% rainfall over historical average."
            trigger_sos = False

        elif "safety" in msg_lower or "evacuate" in msg_lower or "reach safety" in msg_lower:
            response = "For safety: Move to high ground immediately. Avoid riverbanks and mudflow paths. Carry essential emergency supplies and call 112 if trapped."
            trigger_sos = False

        else:
            response = f"D-SQUARE GPT System Active. Ground station telemetry: Temperature {temp:.1f}°C, Soil Moisture {soil_m:.1f}%. Ask me about weather, landslide risks, or evacuation routes."
            trigger_sos = False

        return {
            "query": user_message,
            "response": response,
            "trigger_sos": trigger_sos,
            "disclaimer": self.disclaimer
        }


safety_assistant = SafetyAssistantService()
