import logging
from typing import Dict, Any, List

logger = logging.getLogger("ai-service.engine.dataset")

# Deterministic Delay Logs: Map of Train Number -> Average Delays, Punctuality Ratings, and Cancellation risk
HISTORICAL_TRAIN_DELAYS = {
    "12002": {
        "avg_delay_mins": 12,
        "punctuality_rating": "A",
        "cancellation_rate_percent": 0.5,
        "delay_by_weather": {"clear": 10, "rain": 25, "fog": 120},
    },
    "12434": {
        "avg_delay_mins": 22,
        "punctuality_rating": "B+",
        "cancellation_rate_percent": 1.2,
        "delay_by_weather": {"clear": 15, "rain": 45, "fog": 180},
    },
    "12626": {
        "avg_delay_mins": 48,
        "punctuality_rating": "C-",
        "cancellation_rate_percent": 3.5,
        "delay_by_weather": {"clear": 35, "rain": 90, "fog": 240},
    },
    "22692": {
        "avg_delay_mins": 15,
        "punctuality_rating": "A-",
        "cancellation_rate_percent": 0.8,
        "delay_by_weather": {"clear": 10, "rain": 30, "fog": 150},
    },
    "12860": {
        "avg_delay_mins": 32,
        "punctuality_rating": "B",
        "cancellation_rate_percent": 1.8,
        "delay_by_weather": {"clear": 20, "rain": 60, "fog": 200},
    },
}

# Alternate Station Mapping: Adjacent/Junction stations within ~30km radius for route optimization
ADJACENT_STATIONS_MAP = {
    "BPL": [
        {
            "code": "RKMP",
            "name": "Rani Kamalapati (Habibganj)",
            "distance_km": 6,
            "transfer_time_mins": 15,
        },
        {
            "code": "ET",
            "name": "Itarsi Junction",
            "distance_km": 90,
            "transfer_time_mins": 90,
        },  # major junction alternative
    ],
    "NDLS": [
        {
            "code": "NZM",
            "name": "Hazrat Nizamuddin",
            "distance_km": 7,
            "transfer_time_mins": 25,
        },
        {
            "code": "ANVT",
            "name": "Anand Vihar Terminal",
            "distance_km": 12,
            "transfer_time_mins": 35,
        },
        {
            "code": "DLI",
            "name": "Old Delhi Junction",
            "distance_km": 4,
            "transfer_time_mins": 20,
        },
    ],
    "MAS": [
        {
            "code": "MS",
            "name": "Chennai Egmore",
            "distance_km": 3,
            "transfer_time_mins": 15,
        },
        {"code": "PER", "name": "Perambur", "distance_km": 6, "transfer_time_mins": 20},
    ],
}

# Waitlist Clearance Metrics: clearances profiles by booking class and starting waitlist position
HISTORICAL_WL_CLEARANCE = {
    "3A": {
        "ranges": [
            {"max_wl": 10, "clear_chance": 95, "data_points": 450},
            {"max_wl": 25, "clear_chance": 82, "data_points": 720},
            {"max_wl": 50, "clear_chance": 45, "data_points": 340},
            {"max_wl": 999, "clear_chance": 12, "data_points": 180},
        ]
    },
    "2A": {
        "ranges": [
            {"max_wl": 5, "clear_chance": 90, "data_points": 210},
            {"max_wl": 15, "clear_chance": 75, "data_points": 340},
            {"max_wl": 30, "clear_chance": 38, "data_points": 190},
            {"max_wl": 999, "clear_chance": 8, "data_points": 90},
        ]
    },
    "SL": {
        "ranges": [
            {"max_wl": 20, "clear_chance": 92, "data_points": 890},
            {"max_wl": 50, "clear_chance": 78, "data_points": 1200},
            {"max_wl": 100, "clear_chance": 50, "data_points": 650},
            {"max_wl": 999, "clear_chance": 18, "data_points": 430},
        ]
    },
}


def get_train_delay_metrics(train_number: str) -> Dict[str, Any]:
    """Retrieves synthetic delay and cancellation profile for a train."""
    return HISTORICAL_TRAIN_DELAYS.get(
        train_number,
        {
            "avg_delay_mins": 25,
            "punctuality_rating": "B-",
            "cancellation_rate_percent": 1.5,
            "delay_by_weather": {"clear": 15, "rain": 40, "fog": 160},
        },
    )


def get_adjacent_stations(station_code: str) -> List[Dict[str, Any]]:
    """Retrieves nearby alternative railway stations."""
    return ADJACENT_STATIONS_MAP.get(station_code.strip().upper(), [])


def get_wl_clearance_probability(booking_class: str, current_wl: int) -> Dict[str, Any]:
    """
    Computes confirmation clearance probability (0-100) and returns data density score (0.0-1.0).
    """
    cls = booking_class.strip().upper()
    profile = HISTORICAL_WL_CLEARANCE.get(cls, HISTORICAL_WL_CLEARANCE["3A"])

    for r in profile["ranges"]:
        if current_wl <= r["max_wl"]:
            # Data density represents how much historical data supports the prediction (certainty mapping)
            data_density = min(1.0, r["data_points"] / 1000.0)
            return {
                "probability": r["clear_chance"],
                "data_points": r["data_points"],
                "data_density": data_density,
            }

    return {"probability": 5, "data_points": 50, "data_density": 0.15}
