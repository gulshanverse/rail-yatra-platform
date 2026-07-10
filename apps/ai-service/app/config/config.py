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

    # Configuration loading priority: Env variables -> .env file
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
