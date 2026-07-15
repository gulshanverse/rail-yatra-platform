# app/journey/scoring/engine.py
from typing import Dict, Any
from app.journey.interfaces.contracts import IScoringEngine
from app.journey.dto.models import JourneyCandidateDTO, JourneyRiskDTO, JourneyScoreDTO
from app.journey.config.registry import get_policy


class ScoringEngine(IScoringEngine):
    def compute_scores(
        self,
        candidate: JourneyCandidateDTO,
        risk: JourneyRiskDTO,
        route_intel: Dict[str, Any],
        transfer_intel: Dict[str, Any],
        weights: Dict[str, float],
    ) -> JourneyScoreDTO:
        # 1. Reliability Score ($S_R$)
        reliability = 100.0 * route_intel.get("route_stability", 0.80)

        # 2. Comfort Score ($S_C$)
        comfort = 75.0  # baseline
        # Superfast or express trains are more comfortable
        if any(s.train_number.endswith(("00", "02")) for s in candidate.segments):
            comfort += 20.0

        # 3. Cost Score ($S_F$)
        # Directly proportional to segment counts (fewer transfers means fewer separate fares)
        cost = max(10.0, 100.0 - (len(candidate.segments) * 20.0))

        # 4. Travel Time Score ($S_D$)
        duration = candidate.scheduled_duration_minutes
        time_score = max(10.0, 100.0 - (duration / 10.0))

        # 5. Accessibility Score ($S_A$)
        accessibility = (
            100.0 if not transfer_intel.get("requires_escalator", False) else 70.0
        )

        # 6. Safety Score
        safety = 100.0 * (1.0 - risk.safety_risk_score)

        # 7. Transfer Score
        transfer_score = 100.0
        if len(candidate.transfers) > 0:
            transfer_score = max(
                10.0, 100.0 - (transfer_intel.get("total_walking_minutes", 0) * 5.0)
            )

        # 8. Delay Score
        delay_score = 100.0 * (1.0 - risk.delay_risk_score)

        # 9. Confidence Score
        confidence = 95.0  # mock baseline

        # Get weights from policy if empty
        policy_weights = get_policy("Scoring").get("weights", {})
        w_reliability = weights.get(
            "reliability", policy_weights.get("reliability", 0.30)
        )
        w_comfort = weights.get("comfort", policy_weights.get("comfort", 0.20))
        w_cost = weights.get("cost", policy_weights.get("cost", 0.30))
        w_duration = weights.get("duration", policy_weights.get("duration", 0.20))

        # Normalized Aggregation
        overall = (
            (reliability * w_reliability)
            + (comfort * w_comfort)
            + (cost * w_cost)
            + (time_score * w_duration)
        )
        overall = min(100.0, max(0.0, overall))

        return JourneyScoreDTO(
            overall_score=round(overall, 2),
            reliability_subscore=round(reliability, 2),
            comfort_subscore=round(comfort, 2),
            cost_subscore=round(cost, 2),
            duration_subscore=round(time_score, 2),
            accessibility_subscore=round(accessibility, 2),
            safety_subscore=round(safety, 2),
            transfer_subscore=round(transfer_score, 2),
            delay_subscore=round(delay_score, 2),
            confidence_subscore=round(confidence, 2),
        )
