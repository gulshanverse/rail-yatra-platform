import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # App Settings
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    ENV: str = Field(default="development")

    # DB and Cache Settings
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    QDRANT_URL: str = Field(default="http://localhost:6333")
    SYNC_INTERVAL_SECS: int = Field(default=600, description="Background synchronization interval in seconds")

    # LLM Settings
    DEFAULT_PROVIDER: str = Field(default="openai")  # openai, anthropic, gemini, openrouter, local
    DEFAULT_MODEL: str = Field(default="gpt-4o-mini")

    # API Keys
    OPENAI_API_KEY: str | None = Field(default=None)
    ANTHROPIC_API_KEY: str | None = Field(default=None)
    GOOGLE_API_KEY: str | None = Field(default=None)
    OPENROUTER_API_KEY: str | None = Field(default=None)
    LOCAL_LLM_BASE_URL: str | None = Field(default="http://localhost:11434/v1")  # e.g., Ollama

    # Mock Mode configuration (for local execution without API keys)
    ENABLE_MOCK_LLM: bool = Field(default=True)

    # Memory and Cache Settings
    MEMORY_TTL_SECS: int = Field(default=86400, description="Short-term memory TTL (24 hours)")
    SEMANTIC_CACHE_TTL_SECS: int = Field(default=43200, description="Semantic cache TTL (12 hours)")
    COMPRESSION_THRESHOLD_TOKENS: int = Field(default=4000, description="Trigger context compression above this token size")
    RETRIEVAL_SIMILARITY_THRESHOLD: float = Field(default=0.60, description="Minimum cosine similarity for vector search")
    SEMANTIC_CACHE_THRESHOLD: float = Field(default=0.96, description="Minimum similarity for semantic cache hit")

    # Memory Confidence and Ranking Weights
    WEIGHT_SEMANTIC: float = Field(default=0.50)
    WEIGHT_RECENCY: float = Field(default=0.30)
    WEIGHT_FREQUENCY: float = Field(default=0.10)
    WEIGHT_IMPORTANCE: float = Field(default=0.10)
    DECAY_LAMBDA: float = Field(default=0.005, description="Decay coefficient per hour (half life ~5.7 days)")
    MMR_THETA: float = Field(default=0.65, description="MMR diversity parameter (0.0 to 1.0)")

    # User and Tenant Quotas
    MAX_USER_SHORT_TERM_MESSAGES: int = Field(default=500)
    MAX_USER_LONG_TERM_VECTORS: int = Field(default=2000)
    MAX_TENANT_LONG_TERM_VECTORS: int = Field(default=1000000)
    MAX_ORG_LONG_TERM_VECTORS: int = Field(default=10000000)
    MAX_DAILY_COST_LIMIT: float = Field(default=5.00, description="Max dollar spending limit per user daily")

    # Feature Flags
    SEMANTIC_CACHE_ENABLED: bool = Field(default=True)
    RAG_ENABLED: bool = Field(default=True)
    KNOWLEDGE_GRAPH_ENABLED: bool = Field(default=False)
    MMR_RANKING_ENABLED: bool = Field(default=True)
    CONTEXT_COMPRESSION_ENABLED: bool = Field(default=True)
    EMBEDDING_MIGRATION_ACTIVE: bool = Field(default=False)
    AGENT_SHARED_MEMORY_ENABLED: bool = Field(default=True)

    # Data residency
    DATA_RESIDENCY_REGION: str = Field(default="IN", description="Default geographic residency for storage compliance")

    # Configuration loading priority: Env variables -> .env file
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
