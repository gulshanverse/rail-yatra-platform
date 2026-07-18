# app/personalization/explanations/engine.py
import logging
from typing import Dict, Any
from app.personalization.interfaces.contracts import IExplanationEngine
from app.personalization.dto.models import ReasonCodeDTO, PreferenceEvidenceDTO

logger = logging.getLogger(__name__)


class ExplanationEngine(IExplanationEngine):
    def explain(
        self,
        reason_code: ReasonCodeDTO,
        evidence: PreferenceEvidenceDTO,
        locale: str,
    ) -> Dict[str, Any]:
        template = reason_code.explanation_template
        key = "preference"
        value = "active choice"

        try:
            explanation_str = template.format(key=key, value=value)
        except Exception as e:
            logger.error("Formatting error for template %s: %s", template, e)
            explanation_str = template

        logger.info(
            "Generated explanation under locale=%s: %s", locale, explanation_str
        )
        return {
            "explanation": explanation_str,
            "locale": locale,
            "reason_code": reason_code.code,
            "evidence_id": evidence.evidence_id,
        }
