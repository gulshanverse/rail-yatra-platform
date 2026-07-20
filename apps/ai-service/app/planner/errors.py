# app/planner/errors.py


class PlanningError(Exception):
    """Base exception class for all Planning & Decision Engine errors."""

    pass


class ValidationError(PlanningError):
    """Raised when a plan constraint or validation rule is violated."""

    pass


class SequencingError(PlanningError):
    """Raised when plan step formulation or sequence validation fails."""

    pass


class UnauthorizedFunctionError(PlanningError):
    """Raised when a step references a function that is not approved in the registry."""

    pass


class ClarificationRequiredError(PlanningError):
    """Raised when required parameters are missing or confidence is too low to formulate a plan."""

    pass


class PolicyViolationError(PlanningError):
    """Raised when a plan violates high-level platform or business policies."""

    pass
