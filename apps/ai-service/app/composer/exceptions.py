"""
Composer-specific exceptions for the RailYatra AI Response Composer & Explainability Platform.
Defines the enterprise error catalog (ERR-RSP-001..008).
"""

from typing import Dict, Any, Optional


class ComposerSystemException(Exception):
    """Base exception class for all response composer errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# =====================================================================
# Milestone 6.6 Enterprise Architecture Error Catalog (ERR-RSP-001..008)
# =====================================================================


class ConsentMissingForCompositionException(ComposerSystemException):
    """ERR-RSP-001: Raised when personalized attributes are requested without active DPDP consent."""

    code = "ERR-RSP-001"
    severity = "HIGH"


class ArbitrationFailedException(ComposerSystemException):
    """ERR-RSP-002: Raised when multi-source conflicting data cannot be safely resolved."""

    code = "ERR-RSP-002"
    severity = "HIGH"


class UpstreamTimeoutException(ComposerSystemException):
    """ERR-RSP-003: Raised when upstream intelligence sources exceed the processing latency budget."""

    code = "ERR-RSP-003"
    severity = "MEDIUM"


class CompositionInvariantViolation(ComposerSystemException):
    """ERR-RSP-004: Raised when business rules or aggregate boundary invariants are broken."""

    code = "ERR-RSP-004"
    severity = "CRITICAL"


class PIIMaskingException(ComposerSystemException):
    """ERR-RSP-005: Raised when non-consented PII fails sanitization checks prior to composition."""

    code = "ERR-RSP-005"
    severity = "CRITICAL"


class ExplanationDepthException(ComposerSystemException):
    """ERR-RSP-006: Raised when required explanation depth cannot be generated due to missing groundings."""

    code = "ERR-RSP-006"
    severity = "MEDIUM"


class ResponseValidationException(ComposerSystemException):
    """ERR-RSP-007: Raised when composed response fails scannability or quality validation thresholds."""

    code = "ERR-RSP-007"
    severity = "HIGH"


class IllegalCompositionStateTransition(ComposerSystemException):
    """ERR-RSP-008: Raised when attempting an invalid transition in the composition lifecycle state machine."""

    code = "ERR-RSP-008"
    severity = "HIGH"
