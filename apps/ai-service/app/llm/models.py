from pydantic import BaseModel, Field
from typing import Dict


class ModelMetadata(BaseModel):
    """
    Metadata config describing capabilities and tiers of a specific model.
    """

    provider: str
    model_name: str
    max_tokens: int
    context_window: int
    supports_streaming: bool
    supports_vision: bool
    supports_tool_calling: bool
    supports_json_mode: bool
    supports_function_calling: bool
    pricing_placeholder: Dict[str, float] = Field(
        default_factory=lambda: {"input_cost_per_m": 0.0, "output_cost_per_m": 0.0}
    )
    latency_tier: str  # low, medium, high
    reasoning_tier: str  # standard, high, reasoning


# Central database of model configurations
SUPPORTED_MODELS: Dict[str, ModelMetadata] = {
    # Mock model
    "mock-model": ModelMetadata(
        provider="mock",
        model_name="mock-model",
        max_tokens=2048,
        context_window=8192,
        supports_streaming=True,
        supports_vision=False,
        supports_tool_calling=True,
        supports_json_mode=True,
        supports_function_calling=True,
        latency_tier="low",
        reasoning_tier="standard",
    ),
    # OpenAI models
    "gpt-4o-mini": ModelMetadata(
        provider="openai",
        model_name="gpt-4o-mini",
        max_tokens=4096,
        context_window=128000,
        supports_streaming=True,
        supports_vision=True,
        supports_tool_calling=True,
        supports_json_mode=True,
        supports_function_calling=True,
        latency_tier="low",
        reasoning_tier="standard",
    ),
    "gpt-4o": ModelMetadata(
        provider="openai",
        model_name="gpt-4o",
        max_tokens=4096,
        context_window=128000,
        supports_streaming=True,
        supports_vision=True,
        supports_tool_calling=True,
        supports_json_mode=True,
        supports_function_calling=True,
        latency_tier="medium",
        reasoning_tier="high",
    ),
    # Google Gemini models
    "gemini-1.5-flash": ModelMetadata(
        provider="gemini",
        model_name="gemini-1.5-flash",
        max_tokens=8192,
        context_window=1000000,
        supports_streaming=True,
        supports_vision=True,
        supports_tool_calling=True,
        supports_json_mode=True,
        supports_function_calling=True,
        latency_tier="low",
        reasoning_tier="standard",
    ),
    "gemini-1.5-pro": ModelMetadata(
        provider="gemini",
        model_name="gemini-1.5-pro",
        max_tokens=8192,
        context_window=2000000,
        supports_streaming=True,
        supports_vision=True,
        supports_tool_calling=True,
        supports_json_mode=True,
        supports_function_calling=True,
        latency_tier="high",
        reasoning_tier="high",
    ),
    # Anthropic models
    "claude-3-5-sonnet": ModelMetadata(
        provider="anthropic",
        model_name="claude-3-5-sonnet",
        max_tokens=8192,
        context_window=200000,
        supports_streaming=True,
        supports_vision=True,
        supports_tool_calling=True,
        supports_json_mode=True,
        supports_function_calling=True,
        latency_tier="medium",
        reasoning_tier="high",
    ),
    "claude-3-5-haiku": ModelMetadata(
        provider="anthropic",
        model_name="claude-3-5-haiku",
        max_tokens=4096,
        context_window=200000,
        supports_streaming=True,
        supports_vision=False,
        supports_tool_calling=True,
        supports_json_mode=True,
        supports_function_calling=True,
        latency_tier="low",
        reasoning_tier="standard",
    ),
    # Groq models
    "llama3-8b-8192": ModelMetadata(
        provider="groq",
        model_name="llama3-8b-8192",
        max_tokens=2048,
        context_window=8192,
        supports_streaming=True,
        supports_vision=False,
        supports_tool_calling=True,
        supports_json_mode=True,
        supports_function_calling=True,
        latency_tier="low",
        reasoning_tier="standard",
    ),
    "llama3-70b-8192": ModelMetadata(
        provider="groq",
        model_name="llama3-70b-8192",
        max_tokens=2048,
        context_window=8192,
        supports_streaming=True,
        supports_vision=False,
        supports_tool_calling=True,
        supports_json_mode=True,
        supports_function_calling=True,
        latency_tier="medium",
        reasoning_tier="high",
    ),
    # Azure OpenAI models
    "azure-gpt-4o": ModelMetadata(
        provider="azure",
        model_name="azure-gpt-4o",
        max_tokens=4096,
        context_window=128000,
        supports_streaming=True,
        supports_vision=True,
        supports_tool_calling=True,
        supports_json_mode=True,
        supports_function_calling=True,
        latency_tier="medium",
        reasoning_tier="high",
    ),
    # Ollama local models
    "llama3": ModelMetadata(
        provider="ollama",
        model_name="llama3",
        max_tokens=2048,
        context_window=8192,
        supports_streaming=True,
        supports_vision=False,
        supports_tool_calling=True,
        supports_json_mode=False,
        supports_function_calling=True,
        latency_tier="low",
        reasoning_tier="standard",
    ),
}
