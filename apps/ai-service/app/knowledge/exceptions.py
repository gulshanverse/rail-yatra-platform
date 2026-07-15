"""
Domain-specific exceptions for the Enterprise Knowledge & Embedding Platform.
"""


class KnowledgeException(Exception):
    """Base exception for all Knowledge Platform errors."""

    pass


class KnowledgeSourceException(KnowledgeException):
    """Exception raised when source registration or payload retrieval fails."""

    pass


class IngestionException(KnowledgeException):
    """Exception raised during document validation or ingestion processing."""

    pass


class ProcessingException(KnowledgeException):
    """Exception raised during document cleaning, validation, or PII redaction."""

    pass


class ChunkingException(KnowledgeException):
    """Exception raised during document splitting or chunk validation."""

    pass


class EmbeddingException(KnowledgeException):
    """Exception raised during document/query embedding or model adapter operations."""

    pass


class VectorStoreException(KnowledgeException):
    """Exception raised during vector database interface operations."""

    pass


class VersionMismatchException(KnowledgeException):
    """Exception raised when schemas, embeddings, or indexes are incompatible."""

    pass


class RetrievalException(KnowledgeException):
    """Exception raised when retrieval policy or coordinator execution fails."""

    pass
