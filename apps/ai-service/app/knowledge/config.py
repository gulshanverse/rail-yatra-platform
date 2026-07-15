"""
Configuration management for the Enterprise Knowledge & Embedding Platform.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class KnowledgeSettings(BaseSettings):
    """Configuration schemas for Phase 4.1 Knowledge Platform."""

    CHUNK_SIZE: int = Field(default=512, description="Target chunk token limit")
    CHUNK_OVERLAP: int = Field(
        default=64, description="Overlap offset between contiguous chunks"
    )

    ACTIVE_EMBEDDING_PROVIDER: str = Field(
        default="mock",
        description="Active embedding engine (mock, openai, gemini, local)",
    )
    EMBEDDING_MODEL_NAME: str = Field(
        default="mock-model-v1", description="Model version tag identifier"
    )
    EMBEDDING_DIMENSION: int = Field(
        default=768, description="Output dimensional size of embeddings"
    )

    ACTIVE_VECTOR_STORE: str = Field(
        default="mock", description="Active database adapter (mock, qdrant, pgvector)"
    )
    VECTOR_STORE_CONNECTION_URL: str = Field(
        default="mock://localhost:6333", description="Database target URI"
    )

    INGESTION_BATCH_SIZE: int = Field(
        default=64, description="Size of batch groupings during parallel embeddings"
    )
    INGESTION_MAX_RETRIES: int = Field(
        default=3, description="Maximum pipeline transaction retries"
    )

    QUALITY_THRESHOLD: float = Field(
        default=0.70, description="Minimum acceptable quality threshold score"
    )
    TRUST_THRESHOLD: float = Field(
        default=0.60, description="Minimum trust validation threshold score"
    )
    VIRUS_SCAN_ENABLED: bool = Field(
        default=False, description="Flag control to execute scanner simulation"
    )

    model_config = SettingsConfigDict(env_prefix="KNOWLEDGE_", extra="ignore")


knowledge_settings = KnowledgeSettings()
