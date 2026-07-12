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
