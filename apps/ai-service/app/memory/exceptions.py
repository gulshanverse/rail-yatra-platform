"""
Memory-specific exceptions for the RailYatra AI Memory Layer.
"""


class MemorySystemException(Exception):
    """Base exception class for all memory-related errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class QdrantUnreachable(MemorySystemException):
    """Raised when the connection to Qdrant vector database fails or times out."""

    pass


class RedisCacheMiss(MemorySystemException):
    """Raised when looking up key from Redis fails or returns None in a strict-retrieve context."""

    pass


class TokenLimitExceeded(MemorySystemException):
    """Raised when context size calculation exceeds physical LLM context windows."""

    pass


class ConcurrencyLockError(MemorySystemException):
    """Raised when distributed lock cannot be acquired or experiences race condition errors."""

    pass


class MemoryVersionError(MemorySystemException):
    """Raised when invalid parent trees, rollback requests, or version conflicts occur."""

    pass


class EmbeddingDriftError(MemorySystemException):
    """Raised when embedding quality checks detect mathematical drift beyond threshold bounds."""

    pass


class UserBudgetExceededException(MemorySystemException):
    """Raised when the cost accounting layer detects a user daily spend limit violation."""

    pass


class MemoryQuotaExceededException(MemorySystemException):
    """Raised when user or tenant memory usage quotas are exceeded."""

    pass


class SharedMemoryAccessException(MemorySystemException):
    """Raised when an agent attempts unauthorized access to shared workspaces."""

    pass


class SchemaMigrationException(MemorySystemException):
    """Raised when a schema version migration or compatibility mapping fails."""

    pass


# =====================================================================
# Milestone 6.5 Enterprise Architecture Error Catalog (ERR-MEM-001..007)
# =====================================================================


class ConsentMissingException(MemorySystemException):
    """ERR-MEM-001: Raised when active user consent is missing prior to memory access."""

    code = "ERR-MEM-001"
    severity = "HIGH"


class ConsentWithdrawnException(MemorySystemException):
    """ERR-MEM-002: Raised when attempting read/write operations for a traveler with withdrawn consent."""

    code = "ERR-MEM-002"
    severity = "HIGH"


class InvalidAggregateStateException(MemorySystemException):
    """ERR-MEM-003: Raised when an aggregate root state invariant is violated."""

    code = "ERR-MEM-003"
    severity = "CRITICAL"


class PreferenceConflictException(MemorySystemException):
    """ERR-MEM-004: Raised when new traveler preferences contradict existing preferences without override policy."""

    code = "ERR-MEM-004"
    severity = "MEDIUM"


class SagaExpiredException(MemorySystemException):
    """ERR-MEM-005: Raised when an active booking saga context has exceeded its retention window (>7 days)."""

    code = "ERR-MEM-005"
    severity = "LOW"


class PurgedMemoryAccessException(MemorySystemException):
    """ERR-MEM-006: Raised when attempting to reference or query a purged memory record."""

    code = "ERR-MEM-006"
    severity = "CRITICAL"


class InvariantViolationException(MemorySystemException):
    """ERR-MEM-007: Raised when business rules or aggregate boundary invariants are broken."""

    code = "ERR-MEM-007"
    severity = "CRITICAL"


class IllegalStateTransitionException(MemorySystemException):
    """Raised when attempting an illegal transition in the Memory Lifecycle State Machine."""

    code = "ERR-MEM-008"
    severity = "HIGH"
