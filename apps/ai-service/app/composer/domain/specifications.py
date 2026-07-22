"""
Domain Specifications for Milestone 6.6 AI Response Composer Platform.
Implements the Specification Pattern for business rule validation and query filtering.
"""

from typing import Dict, Any

from app.composer.domain.aggregates import ResponseComposition


class ConsentAwareCompositionSpecification:
    """Specification verifying DPDP consent prior to personal profile injection."""

    def is_satisfied_by(self, consent_data: Dict[str, Any]) -> bool:
        if not consent_data:
            return False
        return consent_data.get("status") == "GRANTED" or consent_data.get("is_granted") is True


class ScannabilitySpecification:
    """Specification validating that composed text adheres to scannability standards."""

    def is_satisfied_by(self, composition: ResponseComposition) -> bool:
        if not composition or not composition.summary:
            return False
        # Scannability check: long outputs (> 50 words) must contain headers, bold, or bullet points
        total_content = " ".join(s.content for s in composition.sections)
        word_count = len(total_content.split())
        if word_count > 50:
            has_headers = "#" in total_content
            has_bold = "**" in total_content
            has_bullets = "-" in total_content or "*" in total_content
            return has_headers or has_bold or has_bullets
        return True


class ConfidenceExplanationRequiredSpecification:
    """Specification determining whether low confidence (< 0.85) requires explicit reasoning nodes."""

    def is_satisfied_by(self, confidence_score: float) -> bool:
        return float(confidence_score) < 0.85


class EmergencyPrioritySpecification:
    """Specification checking if operational disruption warrants emergency priority overriding standard options."""

    def is_satisfied_by(self, operational_status: Dict[str, Any]) -> bool:
        if not operational_status:
            return False
        status_str = str(operational_status.get("status", "")).upper()
        delay_minutes = int(operational_status.get("delay_minutes", 0))
        return status_str in ("CANCELLED", "DIVERTED", "SUSPENDED") or delay_minutes >= 120
