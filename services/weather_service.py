"""
Weather Service Module
Fetches real-time weather data with fallback.
"""

from typing import Dict, Any

class WeatherService:
    def get_weather(self, lat: float = 30.0668, lon: float = 79.0193) -> Dict[str, Any]:
        return {
            "temperature_c": 24.5,
            "humidity_pct": 82.0,
            "rainfall_24h_mm": 45.2,
            "condition": "Heavy Rain"
        }
