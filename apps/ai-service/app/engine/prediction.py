import logging
from typing import Dict, Any
from app.engine.dataset import get_train_delay_metrics, get_wl_clearance_probability

logger = logging.getLogger("ai-service.engine.prediction")

def predict_journey_metrics(
    train_number: str,
    booking_class: str,
    waitlist_position: int | None = None,
    weather_condition: str = "clear"
) -> Dict[str, Any]:
    """
    Computes confirmation probability (0-100), predicted delay minutes,
    and a separate prediction confidence score (0.0-1.0) based on historical density.
    """
    logger.info(f"Predicting metrics for Train {train_number}, class {booking_class}, weather: {weather_condition}")
    
    # 1. Fetch historical delay metrics
    delay_profile = get_train_delay_metrics(train_number)
    base_delay = delay_profile["avg_delay_mins"]
    
    # Adjust delay based on weather
    weather_key = weather_condition.lower()
    weather_delays = delay_profile.get("delay_by_weather", {})
    predicted_delay = weather_delays.get(weather_key, base_delay)
    
    # 2. Fetch waitlist clearing stats if waitlist is present
    confirmation_probability = 100.0
    confidence_score = 0.95  # default high certainty for confirmed status
    
    if waitlist_position and waitlist_position > 0:
        wl_data = get_wl_clearance_probability(booking_class, waitlist_position)
        confirmation_probability = float(wl_data["probability"])
        confidence_score = float(wl_data["data_density"])
    else:
        # If ticket is available/confirmed, we score predictability based on cancellation/delay volatility
        volatility_factor = delay_profile.get("cancellation_rate_percent", 1.0) / 100.0
        confidence_score = max(0.5, round(1.0 - volatility_factor, 2))
        
    return {
        "predicted_delay_mins": int(predicted_delay),
        "confirmation_probability": confirmation_probability,
        "confidence_score": confidence_score
    }
