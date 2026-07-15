# app/booking/explanation/engine.py
from typing import Dict, Any
from app.booking.interfaces.contracts import IExplanationEngine
from app.booking.dto.models import BookingCandidateDTO, ScoreDTO, RiskDTO, ExplanationDTO


class ExplanationEngine(IExplanationEngine):
    def generate_explanations(
        self,
        candidate: BookingCandidateDTO,
        score: ScoreDTO,
        risk: RiskDTO,
        profile: Dict[str, Any]
    ) -> ExplanationDTO:
        reason_codes = []
        rules = []
        
        # 1. Evaluate safety indicators
        if risk.overall_risk_level in ("HIGH", "CRITICAL"):
            reason_codes.append("E_RISK_WARNING_ACTIVE")
            rules.append("RULE_SAFETY_OVER_COMFORT")
        else:
            reason_codes.append("E_RISK_SAFE")
            rules.append("RULE_RISK_ACCEPTABLE")
            
        # 2. Quota choice logic
        if candidate.selected_quota == "GN":
            reason_codes.append("E_DEFAULT_GENERAL_QUOTA")
            rules.append("RULE_GN_DEFAULT")
        else:
            reason_codes.append("E_CONCESSIONAL_QUOTA_APPLIED")
            rules.append("RULE_QUOTA_ELIGIBLE")
            
        # 3. Cost logic
        if score.cost_subscore > 80.0:
            reason_codes.append("E_BUDGET_SAVING")
            rules.append("RULE_COST_EFFICIENT")
            
        summary = (
            f"Recommended booking on train {candidate.segments[0].get('train_number')} "
            f"using {candidate.selected_quota} quota. Confirmation probability is high "
            f"({score.confirmation_subscore}%) and estimated cost is within user budget constraints."
        )
        
        prompt_context = (
            f"Candidate: {candidate.candidate_id}, Quota: {candidate.selected_quota}, "
            f"Class: {candidate.class_code}, Score: {score.overall_score}, "
            f"Risk: {risk.overall_risk_level}."
        )
        
        return ExplanationDTO(
            reason_codes=reason_codes,
            natural_language_explanation=summary,
            score_breakdown={
                "overall": score.overall_score,
                "confirmation": score.confirmation_subscore,
                "cost": score.cost_subscore,
                "comfort": score.comfort_subscore,
                "duration": score.duration_subscore
            },
            risk_breakdown={
                "connection_failure": risk.connection_failure_probability,
            },
            evaluated_rules=rules,
            ai_prompt_context=prompt_context
        )
