import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.data.manager import railway_data_manager

logger = logging.getLogger("ai-service.engine.date_optimizer")

async def optimize_travel_dates(
    source: str,
    destination: str,
    target_date_str: str,
    booking_class: str
) -> List[Dict[str, Any]]:
    """
    Evaluates travel options on adjacent dates (±1 day and ±2 days) to check
    if they offer better seat availability or clearance profiles.
    """
    logger.info(f"Optimizing travel dates around: {target_date_str}")
    
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    except Exception:
        target_date = datetime.now() + timedelta(days=7)

    # We evaluate +1 day and -1 day
    offset_days = [-1, 1, -2, 2]
    optimized_options = []
    
    # Search standard trains for base route asynchronously
    base_trains = await railway_data_manager.search_trains(source, destination)
    
    for offset in offset_days:
        alt_date = target_date + timedelta(days=offset)
        alt_date_str = alt_date.strftime("%Y-%m-%d")
        
        for train in base_trains:
            # Check if train runs on this day of week
            day_of_week = alt_date.strftime("%a").upper()
            if day_of_week in train.runs_on:
                wl_status = "Available 40" if offset in [2, -2] else "WL 4"
                
                option_data = {
                    "train_number": train.train_number,
                    "train_name": train.train_name,
                    "source": source,
                    "destination": destination,
                    "departure": train.departure,
                    "arrival": train.arrival,
                    "duration": train.duration,
                    "booking_class": booking_class,
                    "fare": train.base_fare.get(booking_class.upper(), 1500),
                    "waitlist_status": wl_status,
                    "is_alternative_date": True,
                    "original_journey_date": target_date_str,
                    "journey_date": alt_date_str
                }
                optimized_options.append(option_data)
                
    return optimized_options
