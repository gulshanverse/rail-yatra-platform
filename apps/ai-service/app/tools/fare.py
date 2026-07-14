import logging
from typing import Dict, Any

logger = logging.getLogger("ai-service.tools.fare")


def calculate_fare(
    train_number: str,
    booking_class: str,
    distance_km: int = 500,
    is_tatkal: bool = False,
) -> Dict[str, Any]:
    """
    Computes ticket fares including base fares, dynamic pricing surcharges, Tatkal fees, and GST.
    """
    logger.info(
        f"Calculating fare for train: {train_number}, class: {booking_class}, Tatkal: {is_tatkal}"
    )

    # Simple rate per KM by class
    rates = {"SL": 0.8, "CC": 1.8, "3A": 2.5, "2A": 3.8, "1A": 5.5, "EC": 4.5}

    rate = rates.get(booking_class.upper(), 1.0)
    base_fare = int(distance_km * rate)

    tatkal_charge = 0
    if is_tatkal:
        # Tatkal is usually 10% to 30% of base fare with min/max caps
        tatkal_charge = int(max(100, min(base_fare * 0.3, 500)))

    # Dynamic pricing charge simulation (random but constant for simplicity)
    dynamic_surcharge = (
        int(base_fare * 0.15) if booking_class.upper() in ["3A", "2A", "1A"] else 0
    )

    subtotal = base_fare + tatkal_charge + dynamic_surcharge
    gst = int(subtotal * 0.05) if booking_class.upper() != "SL" else 0
    total_fare = subtotal + gst

    return {
        "success": True,
        "train_number": train_number,
        "booking_class": booking_class.upper(),
        "distance_km": distance_km,
        "base_fare": base_fare,
        "tatkal_charge": tatkal_charge,
        "dynamic_surcharge": dynamic_surcharge,
        "gst_tax": gst,
        "total_fare": total_fare,
        "explanation": f"Fare breakdown: Base fare Rs. {base_fare} + Tatkal Rs. {tatkal_charge} + Dynamic premium Rs. {dynamic_surcharge} + GST Rs. {gst}.",
    }
