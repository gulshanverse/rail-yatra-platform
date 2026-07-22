"""
Domain Specifications for Milestone 6.5 AI Memory Platform.
Implements the Specification Pattern for reusable, composable business rules.
"""

from abc import ABC, abstractmethod
from typing import Any
import time

from app.memory.domain.value_objects import ConsentStatusEnum, RetentionPolicy


class Specification(ABC):
    """Abstract base Specification class supporting boolean composition."""

    @abstractmethod
    def is_satisfied_by(self, candidate: Any) -> bool:
        pass

    def and_spec(self, other: "Specification") -> "AndSpecification":
        return AndSpecification(self, other)

    def or_spec(self, other: "Specification") -> "OrSpecification":
        return OrSpecification(self, other)

    def not_spec(self) -> "NotSpecification":
        return NotSpecification(self)


class AndSpecification(Specification):
    def __init__(self, spec1: Specification, spec2: Specification):
        self.spec1 = spec1
        self.spec2 = spec2

    def is_satisfied_by(self, candidate: Any) -> bool:
        return self.spec1.is_satisfied_by(candidate) and self.spec2.is_satisfied_by(
            candidate
        )


class OrSpecification(Specification):
    def __init__(self, spec1: Specification, spec2: Specification):
        self.spec1 = spec1
        self.spec2 = spec2

    def is_satisfied_by(self, candidate: Any) -> bool:
        return self.spec1.is_satisfied_by(candidate) or self.spec2.is_satisfied_by(
            candidate
        )


class NotSpecification(Specification):
    def __init__(self, spec: Specification):
        self.spec = spec

    def is_satisfied_by(self, candidate: Any) -> bool:
        return not self.spec.is_satisfied_by(candidate)


class ConsentGrantedSpecification(Specification):
    """Specification evaluating if active consent is GRANTED for a candidate."""

    def is_satisfied_by(self, candidate: Any) -> bool:
        if candidate is None:
            return False
        # Candidate can be ConsentProfile aggregate or object with consent_status attribute
        if hasattr(candidate, "consent_status"):
            status_obj = getattr(candidate, "consent_status")
            if hasattr(status_obj, "status"):
                return status_obj.status == ConsentStatusEnum.GRANTED
            return status_obj == ConsentStatusEnum.GRANTED
        if hasattr(candidate, "status"):
            return getattr(candidate, "status") == ConsentStatusEnum.GRANTED
        return False


class EligibleForStorageSpecification(Specification):
    """Specification verifying that candidate memory meets consent and structural rules for storage."""

    def __init__(self):
        self.consent_spec = ConsentGrantedSpecification()

    def is_satisfied_by(self, candidate: Any) -> bool:
        if candidate is None:
            return False

        # Verify candidate has traveler identity
        traveler_id = getattr(candidate, "traveler_id", None)
        if not traveler_id:
            return False

        # Verify consent profile attached or passed
        consent_profile = getattr(candidate, "consent_profile", None)
        if consent_profile is not None:
            if not self.consent_spec.is_satisfied_by(consent_profile):
                return False

        return True


class EligibleForRetrievalSpecification(Specification):
    """Specification verifying that requested memory is active, non-expired, and permitted by consent."""

    def __init__(self):
        self.consent_spec = ConsentGrantedSpecification()

    def is_satisfied_by(self, candidate: Any) -> bool:
        if candidate is None:
            return False

        # Check consent
        consent_profile = getattr(candidate, "consent_profile", None)
        if consent_profile and not self.consent_spec.is_satisfied_by(consent_profile):
            return False

        # Check if purged or explicitly inactive
        if getattr(candidate, "is_purged", False) or getattr(
            candidate, "is_deleted", False
        ):
            return False

        return True


class MemoryExpiredSpecification(Specification):
    """Specification evaluating whether memory exceeds retention policy thresholds."""

    def __init__(self, retention_policy: RetentionPolicy = RetentionPolicy()):
        self.policy = retention_policy

    def is_satisfied_by(self, candidate: Any) -> bool:
        if candidate is None:
            return False

        last_active = getattr(candidate, "last_active_at", None) or getattr(
            candidate, "updated_at", None
        )
        if last_active is None:
            return False

        idle_seconds = time.time() - float(last_active)
        max_idle_seconds = self.policy.idle_expiration_days * 86400

        return idle_seconds > max_idle_seconds
