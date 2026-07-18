# app/personalization/errors.py


class PersonalizationError(Exception):
    """Base exception for personalization domain."""

    def __init__(self, message: str, error_code: str, severity: str = "ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity


class ProfileUnavailable(PersonalizationError):
    def __init__(
        self, message: str = "Traveler profile not found or unavailable."
    ) -> None:
        super().__init__(message, "PERS-001", "ERROR")


class PreferenceConflict(PersonalizationError):
    def __init__(self, message: str = "A preference conflict was detected.") -> None:
        super().__init__(message, "PERS-002", "WARNING")


class MissingConsent(PersonalizationError):
    def __init__(
        self, message: str = "Traveler has not consented to personalization."
    ) -> None:
        super().__init__(message, "PERS-003", "WARNING")


class InvalidObservation(PersonalizationError):
    def __init__(self, message: str = "The logged observation is invalid.") -> None:
        super().__init__(message, "PERS-004", "WARNING")


class ConfidenceTooLow(PersonalizationError):
    def __init__(
        self, message: str = "Confidence score is below the required threshold."
    ) -> None:
        super().__init__(message, "PERS-005", "INFO")


class PolicyViolation(PersonalizationError):
    def __init__(
        self, message: str = "The request violates personalization policies."
    ) -> None:
        super().__init__(message, "PERS-006", "ERROR")


class LearningRejected(PersonalizationError):
    def __init__(self, message: str = "Learning engine logic was rejected.") -> None:
        super().__init__(message, "PERS-007", "INFO")


class ReasonCodeUnavailable(PersonalizationError):
    def __init__(self, message: str = "No valid reason code found.") -> None:
        super().__init__(message, "PERS-008", "WARNING")


class BehaviorUnavailable(PersonalizationError):
    def __init__(
        self, message: str = "Traveler behavior history is unavailable."
    ) -> None:
        super().__init__(message, "PERS-009", "INFO")


class ContextUnavailable(PersonalizationError):
    def __init__(
        self,
        message: str = "Personalization context payload is missing or unavailable.",
    ) -> None:
        super().__init__(message, "PERS-010", "WARNING")


class ConfigurationError(PersonalizationError):
    def __init__(self, message: str = "Configuration registry error.") -> None:
        super().__init__(message, "PERS-011", "CRITICAL")


class AuditFailure(PersonalizationError):
    def __init__(self, message: str = "Audit trail entry commit failed.") -> None:
        super().__init__(message, "PERS-012", "CRITICAL")


class MetricsFailure(PersonalizationError):
    def __init__(self, message: str = "Failed to update metrics store.") -> None:
        super().__init__(message, "PERS-013", "WARNING")


class HealthDegraded(PersonalizationError):
    def __init__(
        self, message: str = "Engine performance or health is degraded."
    ) -> None:
        super().__init__(message, "PERS-014", "CRITICAL")


class ExplanationFailure(PersonalizationError):
    def __init__(self, message: str = "Failed to generate explanation text.") -> None:
        super().__init__(message, "PERS-015", "WARNING")


class InheritanceSkipped(PersonalizationError):
    def __init__(
        self, message: str = "Preference inheritance propagation was skipped."
    ) -> None:
        super().__init__(message, "PERS-016", "INFO")
