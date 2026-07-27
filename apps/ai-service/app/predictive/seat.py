"""
Dynamic Seat Availability Projection Engine (FR-3).
"""

import logging
from app.predictive.interfaces import (
    JourneyContext,
    SeatAvailabilityProjection,
)

logger = logging.getLogger("ai-service.predictive.seat")


class DynamicSeatProjectionEngine:
    """
    Projection engine for seat quota conversion and exhaustion timelines (FR-3).
    """

    async def project_seat_availability(self, journey: JourneyContext) -> SeatAvailabilityProjection:
        # Base available seat projection algorithm
        booking_class = journey.booking_class.upper()
        
        # Seat capacity baselines per class
        class_baseline_seats = {
            "1A": 8,
            "2A": 24,
            "3A": 64,
            "SL": 120,
            "CC": 45,
            "EC": 12,
        }
        
        baseline_available = class_baseline_seats.get(booking_class, 30)
        
        # Exhaustion calculations
        exhaustion_hrs = round(max(1.5, baseline_available * 0.85), 1)
        conversion_rate = round(min(98.0, max(40.0, 100.0 - baseline_available * 0.5)), 1)
        
        trend = "FAST_EXHAUSTION" if baseline_available < 15 else "STABLE_AVAILABILITY"

        logger.info(
            f"Seat projection for Train {journey.train_number} [{booking_class}]: {baseline_available} seats left, exhaustion in {exhaustion_hrs}h"
        )

        return SeatAvailabilityProjection(
            train_number=journey.train_number,
            booking_class=journey.booking_class,
            available_seats=baseline_available,
            projected_exhaustion_hours=exhaustion_hrs,
            quota_conversion_rate=conversion_rate,
            availability_trend=trend,
        )
