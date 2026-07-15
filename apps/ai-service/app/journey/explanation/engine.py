# app/journey/explanation/engine.py
from typing import Dict, Any
from app.journey.interfaces.contracts import IExplanationEngine
from app.journey.dto.models import (
    JourneyCandidateDTO,
    JourneyScoreDTO,
    JourneyRiskDTO,
    JourneyExplanationDTO,
)


class ExplanationEngine(IExplanationEngine):
    def generate_explanation(
        self,
        candidate: JourneyCandidateDTO,
        score: JourneyScoreDTO,
        risk: JourneyRiskDTO,
        traveler_profile: Dict[str, Any],
    ) -> JourneyExplanationDTO:
        reason_codes = []
        evaluated_rules = []

        # 1. Evaluate safety triggers
        if risk.overall_risk_level in ("HIGH", "CRITICAL"):
            reason_codes.append("E_HIGH_RISK_WARNING")
            evaluated_rules.append("RULE_RISK_SAFETY_CAP")

        # 2. Check layout buffer rules
        has_transfers = len(candidate.transfers) > 0
        if has_transfers:
            min_buffer = min(t.buffer_minutes for t in candidate.transfers)
            if min_buffer > 40:
                reason_codes.append("E_BUFFER_SAFE")
                evaluated_rules.append("RULE_TRANSFER_PADDING_OK")
            elif min_buffer < 20:
                reason_codes.append("E_BUFFER_TIGHT")
                evaluated_rules.append("RULE_TRANSFER_PADDING_MINIMUM")
        else:
            reason_codes.append("E_DIRECT_CONNECTION")
            evaluated_rules.append("RULE_NO_TRANSFERS_REQUIRED")

        # 3. Comfort rating rules
        if score.comfort_subscore > 85.0:
            reason_codes.append("E_HIGH_COMFORT")
            evaluated_rules.append("RULE_PREMIUM_COACHES_PREFERRED")

        # 4. Accessibility rules
        if traveler_profile.get("wheelchair_required", False):
            reason_codes.append("E_ACCESSIBLE_PATH")
            evaluated_rules.append("RULE_ADA_STATION_COMPLIANCE")

        # Create natural language summary
        duration_hrs = round(candidate.scheduled_duration_minutes / 60.0, 1)
        if has_transfers:
            summary = (
                f"Connecting journey via JHS takes {duration_hrs} hours total. "
                f"Selected because comfort rating is high ({score.comfort_subscore}) "
                f"and transfer buffer safety matches requirements."
            )
        else:
            summary = (
                f"Direct train candidate completes in {duration_hrs} hours. "
                f"Optimal speed and reliability scoring match user settings."
            )

        # AI-Ready prompt context helper
        ai_context = (
            f"Candidate: {candidate.journey_id}, Score: {score.overall_score}, "
            f"Risk: {risk.overall_risk_level}. Reason Codes: {', '.join(reason_codes)}."
        )

        return JourneyExplanationDTO(
            reason_codes=reason_codes,
            natural_language_explanation=summary,
            score_breakdown={
                "overall": score.overall_score,
                "reliability": score.reliability_subscore,
                "comfort": score.comfort_subscore,
                "cost": score.cost_subscore,
                "duration": score.duration_subscore,
            },
            risk_breakdown={
                "missed_connection_probability": risk.missed_connection_probability,
                "delay_risk": risk.delay_risk_score,
                "weather_risk": risk.weather_risk_score,
                "safety_risk": risk.safety_risk_score,
            },
            evaluated_rules=evaluated_rules,
            ai_prompt_context=ai_context,
        )
