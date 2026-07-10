import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger("ai-service.tools.calendar")

def get_booking_deadlines(journey_date_str: str) -> Dict[str, Any]:
    """
    Computes booking window deadlines:
    - General reservation opens 120 days prior to journey.
    - Tatkal booking opens 1 day prior to journey at 10:00 AM (AC) and 11:00 AM (non-AC).
    """
    logger.info(f"Checking deadlines for journey date: {journey_date_str}")
    try:
        journey_date = datetime.strptime(journey_date_str.split("T")[0], "%Y-%m-%d")
    except Exception as e:
        logger.error(f"Invalid date format: {e}")
        # Default to 7 days from now
        journey_date = datetime.now() + timedelta(days=7)
        
    general_opens = journey_date - timedelta(days=120)
    tatkal_opens = journey_date - timedelta(days=1)
    
    return {
        "success": True,
        "journey_date": journey_date.strftime("%Y-%m-%d"),
        "general_booking_open_date": general_opens.strftime("%Y-%m-%d"),
        "tatkal_booking_date": tatkal_opens.strftime("%Y-%m-%d"),
        "tatkal_ac_window": f"{tatkal_opens.strftime('%Y-%m-%d')} at 10:00 AM IST",
        "tatkal_non_ac_window": f"{tatkal_opens.strftime('%Y-%m-%d')} at 11:00 AM IST",
        "advisory": f"General reservation for this train opened on {general_opens.strftime('%B %d, %Y')}. Tatkal window opens on {tatkal_opens.strftime('%B %d, %Y')}."
    }
