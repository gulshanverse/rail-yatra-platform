import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class LLMSettings(BaseSettings):
    """
    Central configuration settings for the LLM infrastructure layer.
    """
    DEFAULT_PROVIDER: str = Field(default="mock", description="Default LLM provider to resolve.")
    DEFAULT_MODEL: str = Field(default="mock-model", description="Default model name to resolve.")
    
    # Provider keys
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GOOGLE_API_KEY: Optional[str] = Field(default=None)  # Existing project fallback
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    GROQ_API_KEY: Optional[str] = Field(default=None)
    
    # Azure OpenAI configs
    AZURE_OPENAI_KEY: Optional[str] = Field(default=None)
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None)
    AZURE_OPENAI_API_VERSION: str = Field(default="2024-02-15-preview")
    
    # Local client configs
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    
    # Global switches
    ENABLE_MOCK_LLM: bool = Field(default=True, description="Enables Mock Chat client globally for tests/offline runs.")

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

llm_settings = LLMSettings()
