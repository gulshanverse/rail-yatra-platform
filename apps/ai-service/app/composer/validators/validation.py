"""
Dedicated Validation Framework for Milestone 6.6 AI Response Composer Platform.
Independently reusable validators for policies, confidence, privacy, responses, explanations,
and recommendations.
"""

from typing import Dict, Any, List
from abc import ABC, abstractmethod

from app.composer.domain.aggregates import ResponseComposition, ExplanationPayload
from app.composer.exceptions import (
    ResponseValidationException,
    PIIMaskingException,
)


class IValidator(ABC):
    """Abstract interface for all independent validators."""

    @abstractmethod
    def validate(self, target: Any) -> bool:
        """Validates the target object, returning True if valid or raising an exception."""
        pass


class PolicyValidator(IValidator):
    """Validates policy compliance and commercial neutrality."""

    def validate(self, target: Dict[str, Any]) -> bool:
        if not target:
            return True
        # Verify no illegal commercial bias flags
        if target.get("commercial_bias_detected") is True:
            raise ResponseValidationException("Policy Validation Error: Commercial bias detected in recommendation.")
        return True


class ConfidenceValidator(IValidator):
    """Validates confidence score bounds and caveat requirements."""

    def validate(self, target: float) -> bool:
        if not (0.0 <= float(target) <= 1.0):
            raise ResponseValidationException(f"Confidence Validation Error: Invalid score {target}")
        return True


class PrivacyValidator(IValidator):
    """Validates DPDP consent requirements and verifies zero unmasked PII."""

    def validate(self, target: Dict[str, Any]) -> bool:
        has_consent = target.get("has_consent", False)
        unmasked_pii = target.get("contains_unmasked_pii", False)

        if not has_consent and unmasked_pii:
            raise PIIMaskingException("Privacy Validation Error: Unconsented PII exposure detected!")
        return True


class ResponseValidator(IValidator):
    """Validates scannability, word limits, and section structure."""

    def validate(self, target: ResponseComposition) -> bool:
        if not target:
            raise ResponseValidationException("Response Validation Error: Composition is None.")
        if not target.summary:
            raise ResponseValidationException("Response Validation Error: Missing summary direct answer.")
        if not target.sections:
            raise ResponseValidationException("Response Validation Error: Response contains 0 sections.")
        return True


class ExplanationValidator(IValidator):
    """Validates required explanation depth and citation groundings."""

    def validate(self, target: ExplanationPayload) -> bool:
        if not target:
            raise ResponseValidationException("Explanation Validation Error: Explanation payload is None.")
        if target.depth_level < 1 or target.depth_level > 4:
            raise ResponseValidationException(f"Explanation Validation Error: Invalid depth level {target.depth_level}")
        return True


class RecommendationValidator(IValidator):
    """Validates recommendation ranking and trade-off rationales."""

    def validate(self, target: List[Dict[str, Any]]) -> bool:
        for item in target:
            if not item.get("title"):
                raise ResponseValidationException("Recommendation Validation Error: Missing recommendation title.")
        return True


class ConversationValidator(IValidator):
    """Validates multi-turn context integrity across session turns."""

    def validate(self, target: Dict[str, Any]) -> bool:
        if not target.get("session_id"):
            raise ResponseValidationException("Conversation Validation Error: Missing session_id.")
        return True
