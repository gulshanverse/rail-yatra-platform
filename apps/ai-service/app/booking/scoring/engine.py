# app/booking/scoring/engine.py
from typing import Dict
from app.booking.interfaces.contracts import IScoringEngine
from app.booking.dto.models import BookingCandidateDTO, AvailabilityDTO, ConfirmationDTO, RiskDTO, ScoreDTO
from app.booking.config.registry import get_policy


class ScoringEngine(IScoringEngine):
    def compute_booking_score(
        self,
        candidate: BookingCandidateDTO,
        availability: AvailabilityDTO,
        confirmation: ConfirmationDTO,
        risk: RiskDTO,
        weights: Dict[str, float]
    ) -> ScoreDTO:
        # Get defaults weights
        policy_weights = get_policy("Scoring").get("default_weights", {})
        w_confirm = weights.get("confirmation", policy_weights.get("confirmation", 0.40))
        w_cost = weights.get("cost", policy_weights.get("cost", 0.30))
        w_comfort = weights.get("comfort", policy_weights.get("comfort", 0.20))
        w_time = weights.get("time", policy_weights.get("time", 0.10))

        # 1. Confirmation subscore (S_CF)
        s_confirm = 100.0 * confirmation.progression_probability

        # 2. Cost subscore (S_F)
        # Higher fare = lower score
        s_cost = max(10.0, 100.0 - (candidate.estimated_fare / 25.0))

        # 3. Comfort subscore (S_C)
        if candidate.class_code in ("1A", "2A"):
            s_comfort = 95.0
        elif candidate.class_code == "3A":
            s_comfort = 80.0
        else:
            s_comfort = 40.0

        # 4. Travel Time / Duration subscore (S_D)
        s_time = 90.0  # simulated baseline

        # 5. Accessibility subscore
        s_access = 100.0 if candidate.selected_quota != "HP" else 60.0

        # Aggregate weighted score
        overall = (
            (s_confirm * w_confirm) +
            (s_cost * w_cost) +
            (s_comfort * w_comfort) +
            (s_time * w_time)
        )
        overall = min(100.0, max(0.0, overall))

        return ScoreDTO(
            overall_score=round(overall, 2),
            confirmation_subscore=round(s_confirm, 2),
            cost_subscore=round(s_cost, 2),
            comfort_subscore=round(s_comfort, 2),
            duration_subscore=round(s_time, 2),
            accessibility_subscore=round(s_access, 2)
        )
