import logging
from typing import List, Dict, Any

logger = logging.getLogger("ai-service.tools.train_search")

# Simulated trains database representing key corridors
TRAINS_DATABASE = [
    {
        "train_number": "12002",
        "name": "NDLS-BPL Shatabdi Express",
        "source": "NDLS",
        "destination": "BPL",
        "departure": "06:00",
        "arrival": "14:40",
        "duration": "8h 40m",
        "runs_on": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
        "classes": ["CC", "EC"],
        "punctuality": "96% (Avg Delay < 10 mins)",
        "base_fare": {"CC": 1250, "EC": 2450},
    },
    {
        "train_number": "12434",
        "name": "H Nizamuddin - Chennai Central Rajdhani Express",
        "source": "NDLS",
        "destination": "MAS",
        "departure": "15:35",
        "arrival": "20:45",
        "duration": "29h 10m",
        "runs_on": ["WED", "FRI"],
        "classes": ["3A", "2A", "1A"],
        "punctuality": "92% (Avg Delay < 25 mins)",
        "base_fare": {"3A": 2850, "2A": 3950, "1A": 5400},
    },
    {
        "train_number": "12626",
        "name": "Kerala Express",
        "source": "NDLS",
        "destination": "MAS",
        "departure": "20:10",
        "arrival": "04:20",
        "duration": "32h 10m",
        "runs_on": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
        "classes": ["SL", "3A", "2A"],
        "punctuality": "78% (Avg Delay 45 mins)",
        "base_fare": {"SL": 780, "3A": 2100, "2A": 3050},
    },
    {
        "train_number": "22692",
        "name": "Hazrat Nizamuddin - SBC Bengaluru Rajdhani Express",
        "source": "NDLS",
        "destination": "SBC",
        "departure": "19:50",
        "arrival": "05:20",
        "duration": "33h 30m",
        "runs_on": ["MON", "TUE", "FRI", "SAT"],
        "classes": ["3A", "2A", "1A"],
        "punctuality": "94% (Avg Delay < 15 mins)",
        "base_fare": {"3A": 3100, "2A": 4400, "1A": 6100},
    },
    {
        "train_number": "12860",
        "name": "Gitanjali Express",
        "source": "HWH",
        "destination": "CSMT",
        "departure": "14:05",
        "arrival": "21:20",
        "duration": "31h 15m",
        "runs_on": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
        "classes": ["SL", "3A", "2A"],
        "punctuality": "82% (Avg Delay 30 mins)",
        "base_fare": {"SL": 740, "3A": 1980, "2A": 2850},
    },
]


def search_trains(source: str, destination: str) -> List[Dict[str, Any]]:
    """
    Searches simulated database for trains between source and destination stations.
    Supports station code auto-mapping.
    """
    src = source.strip().upper()
    dest = destination.strip().upper()

    logger.info(f"Searching trains from '{src}' to '{dest}'")

    results = []
    for train in TRAINS_DATABASE:
        # Match source and destination station codes
        if train["source"] == src and train["destination"] == dest:
            results.append(train)

    # Return matched trains
    return results
