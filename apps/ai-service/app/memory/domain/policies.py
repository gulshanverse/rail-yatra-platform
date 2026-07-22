"""
Domain Policies for Milestone 6.5 AI Memory Platform.
Encapsulates high-level domain policies for consent, conflict resolution, retention, and privacy.
"""

from typing import Dict, Any, Tuple
import time

from app.memory.domain.value_objects import ConsentStatusEnum, RetentionPolicy
from app.memory.domain.specifications import MemoryExpiredSpecification
from app.memory.exceptions import ConsentMissingException, ConsentWithdrawnException


class ConsentPolicy:
    """Policy enforcing explicit opt-in consent before any memory persistence or recall."""

    @staticmethod
    def enforce_consent(consent_status: ConsentStatusEnum) -> None:
        if consent_status == ConsentStatusEnum.PENDING_VERIFICATION:
            raise ConsentMissingException(
                "BR-MEM-001: Explicit user consent is pending verification."
            )
        if consent_status == ConsentStatusEnum.WITHDRAWN:
            raise ConsentWithdrawnException(
                "BR-MEM-001: User consent is WITHDRAWN. Access denied."
            )


class ConflictResolutionPolicy:
    """Policy governing preference updates when new behavior conflicts with historical data."""

    @staticmethod
    def resolve_preference_conflict(
        existing_val: Any,
        new_val: Any,
        field_name: str,
        override_historical: bool = True,
    ) -> Tuple[Any, bool]:
        """
        Returns (resolved_value, conflict_detected_flag).
        Explicit user selection in active workflow overrides historical preference.
        """
        if existing_val == new_val or new_val is None:
            return existing_val, False

        # Conflict detected
        if override_historical:
            return new_val, True
        return existing_val, True


class RetentionPolicyEvaluator:
    """Evaluates retention policy boundaries for idle expiration and auto-purging."""

    def __init__(self, policy: RetentionPolicy = RetentionPolicy()):
        self.policy = policy
        self.expired_spec = MemoryExpiredSpecification(retention_policy=policy)

    def is_expired(self, last_active_timestamp: float) -> bool:
        idle_seconds = time.time() - last_active_timestamp
        return idle_seconds > (self.policy.idle_expiration_days * 86400)

    def is_exceeded_max_age(self, created_timestamp: float) -> bool:
        age_seconds = time.time() - created_timestamp
        return age_seconds > (self.policy.max_age_days * 86400)


class PrivacyPolicy:
    """Policy providing PII data masking and privacy isolation utilities."""

    @staticmethod
    def mask_pii_string(input_str: str) -> str:
        if not input_str:
            return ""
        cleaned = input_str.strip()
        if len(cleaned) <= 2:
            return "*" * len(cleaned)
        return cleaned[0] + ("*" * (len(cleaned) - 2)) + cleaned[-1]

    @staticmethod
    def sanitize_profile_dict(profile_dict: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = dict(profile_dict)
        if "full_name" in sanitized:
            sanitized["full_name"] = PrivacyPolicy.mask_pii_string(
                sanitized["full_name"]
            )
        if "companions" in sanitized and isinstance(sanitized["companions"], list):
            sanitized_companions = []
            for c in sanitized["companions"]:
                c_copy = dict(c)
                if "name" in c_copy:
                    c_copy["name"] = PrivacyPolicy.mask_pii_string(c_copy["name"])
                sanitized_companions.append(c_copy)
            sanitized["companions"] = sanitized_companions
        return sanitized
