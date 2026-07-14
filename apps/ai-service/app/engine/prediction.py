import logging
from typing import Dict, Any
from app.data.manager import railway_data_manager
from app.engine.dataset import get_wl_clearance_probability

logger = logging.getLogger("ai-service.engine.prediction")


async def predict_journey_metrics(
    train_number: str,
    booking_class: str,
    waitlist_position: int | None = None,
    weather_condition: str = "clear",
) -> Dict[str, Any]:
    """
    Computes confirmation probability (0-100), predicted delay minutes,
    and a separate prediction confidence score (0.0-1.0) using data manager.
    """
    logger.info(
        f"Predicting metrics for Train {train_number}, class {booking_class}, weather: {weather_condition}"
    )

    # 1. Fetch historical delay metrics asynchronously via data manager
    delay_profile = await railway_data_manager.get_delay_history(train_number)

    predicted_delay = 25
    cancellation_rate = 1.0

    if delay_profile:
        predicted_delay = delay_profile.avg_delay_mins
        cancellation_rate = delay_profile.cancellation_rate_percent

        # Adjust delay based on weather
        weather_key = weather_condition.lower()
        if weather_key == "rain":
            predicted_delay = int(predicted_delay * 1.5)
        elif weather_key == "fog":
            predicted_delay = int(predicted_delay * 3.0)

    # 2. Fetch waitlist clearing stats if waitlist is present
    confirmation_probability = 100.0
    confidence_score = 0.95  # default high certainty for confirmed status

    if waitlist_position and waitlist_position > 0:
        wl_data = get_wl_clearance_probability(booking_class, waitlist_position)
        confirmation_probability = float(wl_data["probability"])
        confidence_score = float(wl_data["data_density"])
    else:
        # Volatility index based on cancellation rate
        volatility_factor = cancellation_rate / 100.0
        confidence_score = max(0.5, round(1.0 - volatility_factor, 2))

    return {
        "predicted_delay_mins": predicted_delay,
        "confirmation_probability": confirmation_probability,
        "confidence_score": confidence_score,
    }


Keep = True
