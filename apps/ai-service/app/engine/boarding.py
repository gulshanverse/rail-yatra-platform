import logging
from typing import List, Dict, Any
from app.engine.dataset import get_adjacent_stations
from app.data.manager import railway_data_manager

logger = logging.getLogger("ai-service.engine.boarding")


async def optimize_boarding_stations(
    source: str, destination: str, booking_class: str, journey_date: str
) -> List[Dict[str, Any]]:
    """
    Looks up adjacent/alternative boarding stations for the source station
    and searches for available trains from those station nodes via the data platform.
    """
    logger.info(f"Optimizing boarding stations for source: {source}")
    alternatives = get_adjacent_stations(source)

    optimized_options = []
    for alt in alternatives:
        alt_code = alt["code"]
        logger.info(f"Checking alternative boarding point: {alt_code} ({alt['name']})")

        # Search trains from alternative boarding point to target destination
        matched_trains = await railway_data_manager.search_trains(alt_code, destination)

        for train in matched_trains:
            # Clone and tag as alternative station option
            option_data = {
                "train_number": train.train_number,
                "train_name": train.train_name,
                "source": alt_code,
                "destination": destination,
                "departure": train.departure,
                "arrival": train.arrival,
                "duration": train.duration,
                "booking_class": booking_class,
                "fare": train.base_fare.get(booking_class.upper(), 1500)
                + 50,  # slight distance premium
                "waitlist_status": "Available 12"
                if "Rajdhani" in train.train_name
                else "WL 3",
                "is_alternative_station": True,
                "original_boarding_station": source,
                "journey_date": journey_date,
            }
            optimized_options.append(option_data)

    return optimized_options
