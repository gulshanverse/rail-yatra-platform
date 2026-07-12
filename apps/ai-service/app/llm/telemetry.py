from typing import List, Optional
from pydantic import BaseModel, Field

class TelemetryPayload(BaseModel):
    """
    Telemetry model representing metrics captured for an LLM execution trace.
    No OpenTelemetry exporter bindings are initialized in Batch 1.
    """
    provider: str
    model: str
    latency_ms: float
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    estimated_tokens: int = 0
    estimated_cost: float = 0.0
    retries: int = 0
    errors: List[str] = Field(default_factory=list)
