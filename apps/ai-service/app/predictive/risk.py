"""
Multi-Segment Journey Risk Monitor (FR-6, Capability CP-4).
"""

import logging
from app.predictive.interfaces import (
    JourneyContext,
    RiskEvaluation,
    RiskLevel,
    DelayPrediction,
)

logger = logging.getLogger("ai-service.predictive.risk")


class MultiSegmentRiskMonitor:
    """
    Risk evaluation engine for multi-segment transfer connections (FR-6).
    """

    async def evaluate_connection_risk(
        self, journey: JourneyContext, delay_pred: DelayPrediction
    ) -> RiskEvaluation:
        journey_id = f"J-{journey.train_number}-{journey.origin_station}-{journey.destination_station}"

        if not journey.connecting_train_number or journey.transfer_buffer_mins is None:
            return RiskEvaluation(
                journey_id=journey_id,
                train_number=journey.train_number,
                connecting_train_number=None,
                missed_connection_probability=0.0,
                risk_level=RiskLevel.LOW,
                vulnerability_factors=["SINGLE_SEGMENT_JOURNEY"],
                safety_margin_mins=120,
            )

        transfer_buffer = journey.transfer_buffer_mins
        predicted_delay = delay_pred.predicted_delay_mins

        safety_margin = transfer_buffer - predicted_delay
        vulnerabilities = []

        if safety_margin < 0:
            missed_prob = min(99.0, 85.0 + abs(safety_margin) * 0.5)
            risk_lvl = RiskLevel.CRITICAL
            vulnerabilities.append(f"NEGATIVE_TRANSFER_BUFFER_{safety_margin}M")
        elif safety_margin < 20:
            missed_prob = round(max(50.0, 85.0 - safety_margin * 1.75), 1)
            risk_lvl = RiskLevel.HIGH
            vulnerabilities.append("TIGHT_TRANSFER_WINDOW")
        elif safety_margin < 45:
            missed_prob = round(max(15.0, 45.0 - (safety_margin - 20) * 1.2), 1)
            risk_lvl = RiskLevel.MEDIUM
            vulnerabilities.append("MODERATE_BUFFER_CONSUMPTION")
        else:
            missed_prob = round(max(2.0, 15.0 - (safety_margin - 45) * 0.2), 1)
            risk_lvl = RiskLevel.LOW
            vulnerabilities.append("ADEQUATE_TRANSFER_BUFFER")

        if journey.weather_condition.lower() in ("fog", "storm", "heavy_rain"):
            vulnerabilities.append(f"ADVERSE_WEATHER_{journey.weather_condition.upper()}")

        logger.info(
            f"Risk monitor for {journey.train_number}->{journey.connecting_train_number}: Missed connection prob {missed_prob}% ({risk_lvl.value})"
        )

        return RiskEvaluation(
            journey_id=journey_id,
            train_number=journey.train_number,
            connecting_train_number=journey.connecting_train_number,
            missed_connection_probability=missed_prob,
            risk_level=risk_lvl,
            vulnerability_factors=vulnerabilities,
            safety_margin_mins=safety_margin,
        )
