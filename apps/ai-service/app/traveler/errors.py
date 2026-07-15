# app/traveler/errors.py
"""
Traveler domain error taxonomy (Planning §11).

All domain exceptions inherit from the base ``TravelerError`` class.
"""


class TravelerError(Exception):
    """Base class for all Traveler subsystem errors."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"[{code}] {message}")


class ContextError(TravelerError):
    """ERR_T_CTX – Context creation or validation failure."""

    def __init__(self, message: str = "Context creation failed") -> None:
        super().__init__("ERR_T_CTX", message)


class TimelineError(TravelerError):
    """ERR_T_TIM – Timeline evaluation failure."""

    def __init__(self, message: str = "Timeline evaluation failed") -> None:
        super().__init__("ERR_T_TIM", message)


class CheckpointError(TravelerError):
    """ERR_T_CKP – Checkpoint verification failure."""

    def __init__(self, message: str = "Checkpoint verification failed") -> None:
        super().__init__("ERR_T_CKP", message)


class AlertError(TravelerError):
    """ERR_T_ALT – Alert generation failure."""

    def __init__(self, message: str = "Alert generation failed") -> None:
        super().__init__("ERR_T_ALT", message)


class RecoveryError(TravelerError):
    """ERR_T_REC – Recovery plan generation failure (non-recoverable)."""

    def __init__(self, message: str = "Recovery plan generation failed") -> None:
        super().__init__("ERR_T_REC", message)


class ExplanationError(TravelerError):
    """ERR_T_EXP – Explanation compilation failure."""

    def __init__(self, message: str = "Explanation compilation failed") -> None:
        super().__init__("ERR_T_EXP", message)


class PolicyError(TravelerError):
    """ERR_T_POL – Policy resolution failure (non-recoverable)."""

    def __init__(self, message: str = "Policy resolution failed") -> None:
        super().__init__("ERR_T_POL", message)
