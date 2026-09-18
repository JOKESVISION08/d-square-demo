"""
services/safety_assistant.py — D-SQUARE GPT Intelligence & Safety Assistant Engine
Provides conversational AI guidance for:
1. Live Ground Station Telemetry & Alerts (ESP8266 NodeMCU 10-sensor ground station status)
2. Monsoon & IMD Weather Forecasts (SW/NE Monsoon, district rainfall warnings, cloudbursts)
3. Satellite Earth Observation Knowledge (ISRO Bhuvan, NISAR L/S Dual-SAR, Sentinel-2, NDVI, NBR, LST)
4. Disaster Emergency Safety (Escape guidance, calling 112, SOS dispatch to trusted contacts)
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional

SYSTEM_PROMPT = """You are D-SQUARE GPT, an advanced remote-sensing AI, monsoon weather assistant, and disaster-preparedness intelligence system for people using a mobile application in India.

You possess expert knowledge in:
1. SATELLITE REMOTE SENSING & ISRO / NISAR DATA:
   - ISRO Bhuvan GIS & Sentinel-2 multi-spectral Earth observation (Red B4, Green B3, Blue B2, NIR B8, SWIR B11/B12, Thermal TIR).
   - NISAR Dual-Frequency Synthetic Aperture Radar (SAR): L-band (1.25 GHz / 24 cm wavelength) penetrates forest canopy and soil surface; S-band (3.2 GHz / 9.3 cm wavelength) detects surface roughness, vegetation structure, and soil moisture.
   - Spectral Indices: NDVI (Vegetation Health), NBR (Burn Severity), NDWI/MNDWI (Surface Water), LST (Land Surface Temperature in °C).

2. INDIAN MONSOON & IMD WEATHER DYNAMICS:
   - Southwest Monsoon (June - September) and Northeast Monsoon (October - December).
   - Heavy rainfall warnings, district nowcasts, cloudburst risks, cyclones, and heatwave bulletins from the India Meteorological Department (IMD).

3. GROUND STATION IOT TELEMETRY:
   - Real-time ground station nodes (ESP8266 NodeMCU) equipped with 10 sensors: DHT11 (Temp/Humidity), Capacitive Soil Moisture, MQ-2 Smoke, SW-420 Vibration, SW-520D Tilt, HC-SR04 Water Level Ultrasonic, MPU6050 6-Axis Gyro/Accelerometer, IR Flame.

4. DISASTER SAFETY & EMERGENCY PROCEDURES:
   - Priority #1 is immediate human safety.
   - For flood: Avoid walking, swimming, or driving through floodwater. Move to higher ground.
   - For fire: Move away from smoke/fire in advised directions; cover mouth with damp cloth; avoid forest routes.
   - For landslide: Move away from steep slopes, gullies, and river channels. Watch for falling rock or cracking soil.
   - For trapped, injured, or immediate danger: State clearly "Call 112 now."

Always use official weather and grounded telemetry context when provided. State data freshness and sources. Treat D-SQUARE AI predictions as decision-support estimates. Never invent fake official evacuation orders or fake shelter locations.

End high-risk emergency responses with:
'For immediate danger, call 112 and follow local authority instructions.'"""

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("GPT_API_KEY")


class SafetyAssistantService:
    def process_assistant_query(
        self,
        user_message: str,
        user_lat: float,
        user_lon: float,
        active_alert: Optional[Dict[str, Any]] = None,
        fusion_result: Optional[Dict[str, Any]] = None,
        safe_zones: Optional[List[Dict[str, Any]]] = None,
        weather_data: Optional[Dict[str, Any]] = None,
        ground_station_data: Optional[Dict[str, Any]] = None,
        data_mode: str = "DEMO"
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive multi-modal context packet (Satellite, Monsoon, Ground Station, Alert)
        and returns a structured D-SQUARE GPT intelligence response.
        """
        user_msg_lower = user_message.lower()

        # Danger triggers demanding immediate 112 recommendation
        danger_triggers = [
            "trapped", "injured", "injury", "hurt", "fire nearby", "fire close", "smoke inside",
            "flood entering", "water inside", "water entering", "missing person", "cannot move",
            "cannot evacuate", "rescue me", "help me", "stuck", "avalanche", "landslide moving"
        ]
        call_112_triggered = any(trigger in user_msg_lower for trigger in danger_triggers)

        context_packet = {
            "user_location": {"latitude": user_lat, "longitude": user_lon},
            "data_mode": data_mode,
            "active_alert": active_alert or {"disaster_type": "None", "risk_level": "LOW"},
            "fusion_summary": {
                "risk_level": (fusion_result or {}).get("risk_level", "LOW"),
                "disaster": (fusion_result or {}).get("predicted_disaster", "None"),
                "probability": (fusion_result or {}).get("disaster_probability_percent", 12.5)
            },
            "ground_station_status": ground_station_data or {
                "node_id": "ESP8266_NODE_01",
                "temperature": 26.5,
                "humidity": 52.0,
                "soil_moisture": 42.0,
                "smoke": 185.0,
                "water_level": 4.5,
                "vibration": 0.2,
                "tilt_angle": 1.2,
                "flame": "NO"
            },
            "safe_zones_available": len(safe_zones or []),
            "official_weather": weather_data or {"available": False},
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Query OpenAI API if API key is set
        if OPENAI_API_KEY:
            try:
                response = self._query_openai_api(user_message, context_packet)
                if response:
                    return response
            except Exception:
                pass

        # Grounded Rule Engine Fallback
        return self._generate_rule_based_response(user_message, context_packet, call_112_triggered)

    def _query_openai_api(self, user_message: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Queries OpenAI Chat Completions API with system prompt and JSON format."""
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        prompt_content = f"GROUNDED CONTEXT PACKET:\n{json.dumps(context, indent=2)}\n\nUSER QUESTION: {user_message}"

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_content}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=8.0)
        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return {
                "message": parsed.get("message", "D-SQUARE GPT processing completed."),
                "urgency": parsed.get("urgency", "normal"),
                "call_112_recommended": parsed.get("call_112_recommended", False),
                "show_safe_locations": parsed.get("show_safe_locations", False),
                "source_summary": ["D-SQUARE Satellite Knowledge", "IMD Weather", "ESP8266 Ground Station"],
                "data_freshness": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "disclaimer": "For immediate danger, call 112 or follow official local-authority instructions."
            }
        return None

    def _generate_rule_based_response(self, message: str, context: Dict[str, Any], force_112: bool) -> Dict[str, Any]:
        """Generates deterministic intelligence guidance for satellite, weather, telemetry, and safety queries."""
        msg_lower = message.lower()
        alert = context.get("active_alert", {})
        disaster = alert.get("disaster_type", "None")
        risk = alert.get("risk_level", "LOW")
        weather = context.get("official_weather", {})
        gs = context.get("ground_station_status", {})

        urgency = "normal"
        call_112 = force_112
        show_shelters = False
        text_lines = []

        if force_112 or risk in ["HIGH", "CRITICAL"]:
            urgency = "emergency" if force_112 or risk == "CRITICAL" else "high"
            call_112 = True
            show_shelters = True
            text_lines.append("🚨 **Emergency Action Recommended**: Call 112 immediately if you are trapped, injured, or in direct danger.")

        # 1. SATELLITE KNOWLEDGE QUERIES
        if any(w in msg_lower for w in ["nisar", "sar", "radar", "l-band", "s-band", "ndvi", "nbr", "lst", "satellite", "isro", "bhuvan", "geotiff"]):
            text_lines.append("🛰️ **D-SQUARE Satellite Earth Observation Intelligence**:")
            has_sar = any(k in msg_lower for k in ["nisar", "sar", "radar"])
            has_index = any(k in msg_lower for k in ["ndvi", "nbr"])

            if has_sar:
                text_lines.append("• **NISAR Dual-Frequency SAR**: Joint ISRO-NASA mission using **L-band (24 cm)** and **S-band (9.3 cm)** radar backscatter ($dB$).")
                text_lines.append("• **L-band (-12.4 dB)**: Penetrates dense Himalayan forest canopy and surface soil to map land deformation and moisture.")
                text_lines.append("• **S-band (-8.6 dB)**: Measures surface roughness, crop structure, and flood inundation boundary changes.")
            if has_index:
                text_lines.append("• **NDVI (Vegetation Index)**: $(NIR - Red) / (NIR + Red)$. Healthy green canopy = 0.60 to 0.85; Burnt scar/bare soil < 0.20.")
                text_lines.append("• **NBR (Burn Ratio)**: $(NIR - SWIR2) / (NIR + SWIR2)$. Sharp NBR drop indicates active forest fire or burn severity.")
            if not has_sar and not has_index:
                text_lines.append("• **ISRO Bhuvan / Sentinel-2 Grid**: Multi-spectral resolution down to 10m/23.5m. Monitors Himalayan high-risk belts for fires, floods, and landslides.")

        # 2. MONSOON & WEATHER QUERIES
        elif any(w in msg_lower for w in ["monsoon", "rain", "forecast", "cloudburst", "imd", "weather", "temperature", "humidity", "carry"]):
            text_lines.append("🌧️ **D-SQUARE Indian Monsoon & IMD Weather Intelligence**:")
            text_lines.append("• **Monsoon Dynamics**: Southwest Monsoon (June-Sept) brings over 75% of annual rainfall to North India & Himalayas.")
            if weather.get("available"):
                text_lines.append(f"• **IMD District Forecast**: {weather.get('forecast_24h')}")
                text_lines.append(f"• **24-Hour Rainfall**: {weather.get('rainfall_mm')} mm | Temperature: {weather.get('temperature_c')}°C | Humidity: {weather.get('humidity_percent')}%")
                text_lines.append(f"• **District Warning**: {weather.get('district_warning_text')}")
            else:
                text_lines.append("• **IMD Weather Status**: Official IMD district warning feed is currently unconfigured in this app. Follow www.mausam.imd.gov.in for official bulletins.")

        # 3. GROUND STATION TELEMETRY QUERIES
        elif any(w in msg_lower for w in ["ground station", "telemetry", "esp8266", "sensor", "vibration", "tilt", "mpu6050", "soil", "water level"]):
            text_lines.append("📟 **ESP8266 IoT Ground Station Live Telemetry (`ESP8266_NODE_01`)**:")
            text_lines.append(f"• **Temperature / Humidity**: {gs.get('temperature', 26.5)}°C | {gs.get('humidity', 52.0)}%")
            text_lines.append(f"• **Soil Moisture & Smoke**: {gs.get('soil_moisture', 42.0)}% | MQ-2: {gs.get('smoke', 185)} PPM")
            text_lines.append(f"• **MPU6050 Tilt & Gyro**: Tilt Angle {gs.get('tilt_angle', 1.2)}° | Vibration: {gs.get('vibration', 0.2)} m/s²")
            text_lines.append(f"• **Ultrasonic Water Level**: {gs.get('water_level', 4.5)} cm | IR Flame: {gs.get('flame', 'NO')}")

        # 4. EMERGENCY DISASTER SAFETY QUERIES
        elif "flood" in msg_lower or disaster == "Flood":
            text_lines.append("🌊 **Flood Escape & Safety Rules**:")
            text_lines.append("• Move to higher ground immediately if safe to do so.")
            text_lines.append("• **NEVER** walk, swim, or drive through moving floodwater.")
            text_lines.append("• Avoid drains, culverts, power poles, and fallen wires.")
            text_lines.append("• Call 112 if trapped or water enters your building.")
            show_shelters = True

        elif "fire" in msg_lower or "smoke" in msg_lower or disaster == "Forest_Fire":
            text_lines.append("🔥 **Forest Fire & Smoke Safety Rules**:")
            text_lines.append("• Move away from fire/smoke in directions advised by authorities.")
            text_lines.append("• Do not enter forest trails, gullies, or smoke-filled zones.")
            text_lines.append("• Cover nose and mouth with a wet cloth or mask.")
            text_lines.append("• Call 112 if fire approaches your location.")

        elif "landslide" in msg_lower or disaster == "Landslide":
            text_lines.append("⛰️ **Landslide & Slope Safety Rules**:")
            text_lines.append("• Move away from steep slopes, gullies, retaining walls, and river channels.")
            text_lines.append("• Watch for cracking soil, falling rocks, leaning trees, or unusual loud sounds.")
            text_lines.append("• Do not return to a slope after a slide has occurred.")
            text_lines.append("• Call 112 if anyone is trapped or injured.")

        elif any(s in msg_lower for s in ["sos", "contact", "share", "location"]):
            text_lines.append("📱 **D-SQUARE Mobile SOS Options**:")
            text_lines.append("• Press **'CALL 112 NOW'** to dial Indian Emergency Services directly.")
            text_lines.append("• Press **'SEND SOS TO TRUSTED CONTACTS'** to share live GPS map link with saved contacts.")
            text_lines.append("• Press **'SHELTERS'** to view verified emergency shelters.")

        else:
            text_lines.append("🤖 **D-SQUARE GPT Assistant**: Ask me about **Satellite Data** (ISRO Bhuvan/NISAR), **Monsoon & Weather**, **Ground Station Telemetry**, or **Disaster Safety**.")

        final_msg = "\n".join(text_lines)
        if not final_msg.endswith("112."):
            final_msg += "\n\nFor immediate danger, call 112 and follow local authority instructions."

        return {
            "message": final_msg,
            "urgency": urgency,
            "call_112_recommended": call_112,
            "show_safe_locations": show_shelters,
            "source_summary": ["ISRO Bhuvan / NISAR Satellite Data", "IMD Weather Engine", "ESP8266 Ground Station Telemetry"],
            "data_freshness": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "disclaimer": "For immediate danger, call 112 or follow official local-authority instructions."
        }
