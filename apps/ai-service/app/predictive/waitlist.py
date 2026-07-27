"""
Waitlist Confirmation Forecaster (FR-1, Capability CP-2).
"""

import math
import logging
from app.predictive.interfaces import (
    JourneyContext,
    WaitlistPrediction,
    ConfidenceLevel,
)

logger = logging.getLogger("ai-service.predictive.waitlist")


class WaitlistForecaster:
    """
    Forecasting engine for seat waitlist confirmation probabilities (FR-1).
    Computes confirmation odds (0-100%) and confidence levels.
    """

    # Class-specific clearance rates per day prior to departure
    CLASS_CLEARANCE_RATES = {
        "1A": 0.45,
        "2A": 0.65,
        "3A": 0.82,
        "SL": 0.90,
        "CC": 0.75,
        "EC": 0.50,
        "3E": 0.85,
    }

    # Quota modifiers
    QUOTA_MODIFIERS = {
        "GN": 1.0,
        "TQ": 0.4,
        "LD": 0.7,
        "HO": 0.9,
    }

    async def predict_confirmation(self, journey: JourneyContext) -> WaitlistPrediction:
        position = journey.waitlist_position or 0
        if position <= 0:
            return WaitlistPrediction(
                train_number=journey.train_number,
                booking_class=journey.booking_class,
                waitlist_position=0,
                confirmation_probability=100.0,
                confidence_score=0.98,
                confidence_level=ConfidenceLevel.HIGH,
                clearing_trend="CONFIRMED",
                estimated_clearance_days=0.0,
                historical_data_density=2500,
            )

        base_rate = self.CLASS_CLEARANCE_RATES.get(journey.booking_class.upper(), 0.70)
        quota_mod = self.QUOTA_MODIFIERS.get(journey.quota.upper(), 1.0)
        effective_rate = base_rate * quota_mod

        # Calculate decay based on position
        decay_factor = math.exp(-0.035 * position / max(0.1, effective_rate))
        prob = round(max(2.0, min(99.0, decay_factor * 100.0)), 1)

        # Confidence calculation
        if position <= 15:
            confidence_score = 0.92
            confidence_lvl = ConfidenceLevel.HIGH
            trend = "STRONG_CLEARANCE"
        elif position <= 50:
            confidence_score = 0.84
            confidence_lvl = ConfidenceLevel.MEDIUM
            trend = "MODERATE_CLEARANCE"
        else:
            confidence_score = 0.68
            confidence_lvl = ConfidenceLevel.LOW
            trend = "SLOW_CLEARANCE"

        estimated_days = round(position / (effective_rate * 12.0), 1)

        logger.info(
            f"Waitlist forecast for Train {journey.train_number} WL{position} [{journey.booking_class}]: {prob}% ({confidence_lvl.value})"
        )

        return WaitlistPrediction(
            train_number=journey.train_number,
            booking_class=journey.booking_class,
            waitlist_position=position,
            confirmation_probability=prob,
            confidence_score=confidence_score,
            confidence_level=confidence_lvl,
            clearing_trend=trend,
            estimated_clearance_days=estimated_days,
            historical_data_density=1420,
        )
