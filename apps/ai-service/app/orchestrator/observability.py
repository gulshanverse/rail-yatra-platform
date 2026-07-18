import logging
import time
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.orchestrator.events import event_bus, AIEvent

logger = logging.getLogger("ai-service.orchestrator.observability")


class DecisionTrace(BaseModel):
    """
    Structured trace details generated per decision run for compliance and audit.
    """

    trace_id: str
    conversation_id: str
    user_id: str
    input_message: str
    routing_decision: str
    confidence: float
    policy_evaluations: List[str] = Field(default_factory=list)
    fallback_applied: bool = False
    fallback_reason: Optional[str] = None
    execution_success: bool = True
    execution_time_ms: float = 0.0
    timestamp: float = Field(default_factory=time.time)


class CostTrace(BaseModel):
    """
    Token, duration, and financial metrics recorded for each transaction execution.
    """

    trace_id: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    provider: str = "unknown"
    execution_duration_s: float = 0.0
    estimated_cost_usd: float = 0.0


class AIObservabilityFramework:
    """
    Subsystem collecting tracing metrics and dispatching event bus broadcasts.
    """

    def __init__(self) -> None:
        self._traces: Dict[str, DecisionTrace] = {}
        self._costs: Dict[str, CostTrace] = {}

    def record_decision(self, trace: DecisionTrace) -> None:
        """Saves decision trace and publishes the telemetry event."""
        self._traces[trace.trace_id] = trace
        logger.info(f"Recorded decision trace: {trace.trace_id} (routing={trace.routing_decision})")

        # Publish tracing event to Event Bus
        event = AIEvent(
            event_type="decision_trace",
            payload=trace.model_dump(),
            trace_id=trace.trace_id,
            correlation_id=trace.trace_id,
        )
        # Run async publish inside run-loop
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(event_bus.publish(event))
        except Exception as e:
            logger.warning(f"Could not dispatch decision trace event: {e}")

    def record_cost(self, cost: CostTrace) -> None:
        """Saves transaction cost metrics and publishes telemetry metrics."""
        self._costs[cost.trace_id] = cost
        logger.info(
            f"Recorded cost metrics: {cost.trace_id} (tokens={cost.total_tokens}, cost=${cost.estimated_cost_usd:.5f})"
        )

        event = AIEvent(
            event_type="cost_metrics",
            payload=cost.model_dump(),
            trace_id=cost.trace_id,
            correlation_id=cost.trace_id,
        )
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(event_bus.publish(event))
        except Exception as e:
            logger.warning(f"Could not dispatch cost metrics event: {e}")

    def get_trace(self, trace_id: str) -> Optional[DecisionTrace]:
        """Retrieves a specific decision trace by ID."""
        return self._traces.get(trace_id)

    def get_cost(self, trace_id: str) -> Optional[CostTrace]:
        """Retrieves cost metrics by ID."""
        return self._costs.get(trace_id)


# Global singleton observability manager
observability_framework = AIObservabilityFramework()
