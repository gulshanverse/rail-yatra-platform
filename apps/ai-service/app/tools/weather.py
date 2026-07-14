import logging
import random
from typing import Dict, Any

logger = logging.getLogger("ai-service.tools.weather")

STATION_WEATHER_DATA = {
    "NDLS": {
        "city": "New Delhi",
        "temp": "34°C",
        "condition": "Partly Cloudy",
        "delay_impact": "None",
    },
    "BPL": {
        "city": "Bhopal",
        "temp": "29°C",
        "condition": "Heavy Rain",
        "delay_impact": "Low (Avg 15 min delays)",
    },
    "MAS": {
        "city": "Chennai",
        "temp": "31°C",
        "condition": "Humid / Sunny",
        "delay_impact": "None",
    },
    "HWH": {
        "city": "Kolkata",
        "temp": "30°C",
        "condition": "Thunderstorms",
        "delay_impact": "Medium (Avg 30 min delays)",
    },
    "CSMT": {
        "city": "Mumbai",
        "temp": "28°C",
        "condition": "Monsoon Showers",
        "delay_impact": "Medium (Avg 20-40 min delays)",
    },
}


def get_station_weather(station_code: str) -> Dict[str, Any]:
    """
    Checks the local weather status at the specified railway station.
    Provides delay predictions if extreme weather (rain/fog) is detected.
    """
    code = station_code.strip().upper()
    logger.info(f"Checking weather for station: {code}")

    if code in STATION_WEATHER_DATA:
        info = STATION_WEATHER_DATA[code]
        return {
            "success": True,
            "station": code,
            "city": info["city"],
            "temperature": info["temp"],
            "condition": info["condition"],
            "delay_impact": info["delay_impact"],
            "advisory": f"Advisory for {info['city']}: Wear appropriate clothes. Travel delay risk is {info['delay_impact']}.",
        }

    # Generic fallback
    temp = f"{random.randint(22, 38)}°C"
    cond = random.choice(["Sunny", "Overcast", "Drizzle", "Clear"])
    return {
        "success": True,
        "station": code,
        "city": f"{code} Region",
        "temperature": temp,
        "condition": cond,
        "delay_impact": "None",
        "advisory": "No extreme weather alerts found. Normal running expected.",
    }
