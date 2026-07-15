# app/journey/risk/engine.py
from typing import Dict, Any
from app.journey.interfaces.contracts import IRiskEngine
from app.journey.dto.models import JourneyCandidateDTO, JourneyRiskDTO


class RiskEngine(IRiskEngine):
    def calculate_risk(
        self,
        candidate: JourneyCandidateDTO,
        route_intel: Dict[str, Any],
        transfer_intel: Dict[str, Any],
        traveler_profile: Dict[str, Any]
    ) -> JourneyRiskDTO:
        risk_factors = []
        
        # 1. Delay risk scoring based on historical averages
        avg_delay = route_intel.get("average_delay_minutes", 10.0)
        delay_risk = min(1.0, avg_delay / 120.0)
        if avg_delay > 45.0:
            risk_factors.append("HIGH_HISTORICAL_DELAYS")

        # 2. Transfer missed connection risk
        missed_prob = transfer_intel.get("missed_connection_probability", 0.0)
        if missed_prob > 0.40:
            risk_factors.append("TIGHT_TRANSFER_WINDOW")
        elif missed_prob > 0.15:
            risk_factors.append("MODERATE_TRANSFER_WINDOW")

        # 3. Weather risk
        weather_alert_level = traveler_profile.get("weather_alert_level", "NONE")
        weather_risk = 0.0
        if weather_alert_level == "RED":
            weather_risk = 0.90
            risk_factors.append("CRITICAL_WEATHER_WARNING")
        elif weather_alert_level == "YELLOW":
            weather_risk = 0.40
            risk_factors.append("WEATHER_ALERT_ACTIVE")

        # 4. Safety risk
        safety_risk = 0.05
        # Late night halts in minor terminals
        if len(candidate.transfers) > 0 and route_intel.get("station_complexity", 0) > 0.60:
            safety_risk = 0.35
            risk_factors.append("LATE_NIGHT_LAYOVER")

        # Aggregate risk calculation using mathematical hazard models
        # Overall risk level determination
        aggregate_probability = 1.0 - (
            (1.0 - delay_risk) * (1.0 - missed_prob) * (1.0 - weather_risk) * (1.0 - safety_risk)
        )
        aggregate_probability = min(1.0, max(0.0, aggregate_probability))

        if aggregate_probability > 0.70:
            overall_level = "CRITICAL"
        elif aggregate_probability > 0.40:
            overall_level = "HIGH"
        elif aggregate_probability > 0.15:
            overall_level = "MEDIUM"
        else:
            overall_level = "LOW"

        return JourneyRiskDTO(
            overall_risk_level=overall_level,
            missed_connection_probability=missed_prob,
            delay_risk_score=round(delay_risk, 2),
            weather_risk_score=round(weather_risk, 2),
            safety_risk_score=round(safety_risk, 2),
            risk_factors=risk_factors
        )
