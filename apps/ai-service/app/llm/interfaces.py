from typing import Dict, Any, List, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage


class GenerationOptions(BaseModel):
    """Configuration options for model generation (temperature, max tokens, etc.)."""

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    stop: Optional[List[str]] = Field(default=None)
    json_mode: bool = Field(default=False)
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Encapsulates payload for a chat completion request."""

    messages: List[BaseMessage]
    model: str
    options: GenerationOptions = Field(default_factory=GenerationOptions)


class CostMetadata(BaseModel):
    """Cost details for pricing estimation."""

    input_cost_per_m: float = Field(default=0.0)
    output_cost_per_m: float = Field(default=0.0)
    estimated_request_cost: float = Field(default=0.0)


class ChatResponse(BaseModel):
    """Standardized response format returned by all providers."""

    content: str
    model: str
    provider: str
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    cost: CostMetadata = Field(default_factory=CostMetadata)
    raw_response: Optional[Dict[str, Any]] = Field(default=None)


class CapabilityMetadata(BaseModel):
    """Capability flags for a model/provider configuration."""

    supports_streaming: bool = Field(default=False)
    supports_vision: bool = Field(default=False)
    supports_json_mode: bool = Field(default=False)
    supports_tool_calling: bool = Field(default=False)
    supports_function_calling: bool = Field(default=False)
    context_window_tokens: int = Field(default=4096)


class ProviderMetadata(BaseModel):
    """Metadata describing provider information and static capabilities."""

    name: str
    supported_models: List[str]
    is_local: bool
    capabilities: Dict[str, CapabilityMetadata] = Field(default_factory=dict)


class HealthMetadata(BaseModel):
    """Status report details mapping provider availability."""

    configured: bool
    available: bool
    authenticated: bool
    healthy: bool
    latency_ms: float
    version: Optional[str] = None


@runtime_checkable
class TelemetryEvents(Protocol):
    """
    Protocol mapping telemetry event recording.
    """

    def log_event(self, name: str, payload: Dict[str, Any]) -> None: ...


@runtime_checkable
class LLMProvider(Protocol):
    """
    Interface definition for an LLM Provider integration.
    """

    @property
    def name(self) -> str: ...
    def get_metadata(self) -> ProviderMetadata: ...
    async def check_health(self) -> HealthMetadata: ...
    async def generate(self, request: ChatRequest) -> ChatResponse: ...
