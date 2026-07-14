import logging
import random
from typing import Dict, Any

logger = logging.getLogger("ai-service.tools.pnr")


def get_pnr_status(pnr: str) -> Dict[str, Any]:
    """
    Checks the status of the specified 10-digit Indian Railways PNR number.
    Generates realistic, consistent mock status metrics.
    """
    clean_pnr = pnr.strip()
    logger.info(f"Checking status for PNR: {clean_pnr}")

    if len(clean_pnr) != 10 or not clean_pnr.isdigit():
        return {
            "success": False,
            "error": "Invalid PNR format. Must be a 10-digit numeric code.",
        }

    # Generate consistent results based on PNR string to simulate actual records
    seed = sum(int(char) for char in clean_pnr)
    random.seed(seed)

    trains = [
        {"num": "12002", "name": "Bhopal Shatabdi", "class": "CC"},
        {"num": "12626", "name": "Kerala Express", "class": "3A"},
        {"num": "12434", "name": "Chennai Rajdhani", "class": "2A"},
    ]
    train = random.choice(trains)

    wl_start = random.randint(10, 45)
    wl_current = max(1, wl_start - random.randint(5, 20))
    chart_prepared = wl_current == 1 or random.choice([True, False])

    status_types = ["WL", "RAC", "CNF"]
    current_status_type = random.choice(status_types)

    if current_status_type == "CNF":
        curr_status = "CNF (Coach B2, Berth 24)"
        prob = 100.0
    elif current_status_type == "RAC":
        curr_status = f"RAC {random.randint(1, 10)}"
        prob = 95.0
    else:
        curr_status = f"WL {wl_current}"
        # confirmation probability prediction
        prob = round(max(10.0, 100.0 - (wl_current * 2.2)), 1)

    return {
        "success": True,
        "pnr": clean_pnr,
        "train_number": train["num"],
        "train_name": train["name"],
        "journey_date": "2026-07-28",
        "booking_class": train["class"],
        "chart_status": "Chart Prepared" if chart_prepared else "Chart Not Prepared",
        "passengers": [
            {
                "passenger_number": 1,
                "booking_status": f"WL {wl_start}",
                "current_status": curr_status,
            }
        ],
        "confirmation_probability": f"{prob}%",
        "delay_prediction": f"{random.randint(0, 45)} mins",
    }


Keep = True
