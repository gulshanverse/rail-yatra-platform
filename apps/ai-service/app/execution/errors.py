# app/execution/errors.py


class ExecutionError(Exception):
    """Base exception class for all Execution Engine errors."""

    pass


class InvalidStateTransitionError(ExecutionError):
    """Raised when an execution session state transition violates lifecycle invariants."""

    pass


class IdempotencyViolationError(ExecutionError):
    """Raised when a duplicate execution token is processed."""

    pass


class StepExecutionFailedError(ExecutionError):
    """Raised when a plan step fails after all retry attempts are exhausted."""

    pass


class CompensationFailedError(ExecutionError):
    """Raised when a compensating transaction fails during rollback."""

    pass


class AuthorizationFailedError(ExecutionError):
    """Raised when traveler authorization context checks fail."""

    pass
