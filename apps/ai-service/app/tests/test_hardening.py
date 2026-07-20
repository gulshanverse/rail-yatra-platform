import pytest
from typing import Dict, Any, AsyncIterator
from app.orchestrator.state import AIState
from app.orchestrator.interfaces import IAgent
from app.orchestrator.registry import agent_registry
from app.orchestrator.capabilities import capability_registry, CapabilityMetadata
from app.orchestrator.events import event_bus, AIEvent
from app.orchestrator.config import platform_config
from app.orchestrator.observability import (
    observability_framework,
    DecisionTrace,
    CostTrace,
)
from app.orchestrator.policy import policy_engine, governance_layer


class MockTestAgent(IAgent):
    name: str = "MockTestAgent"
    system_prompt: str = "Test system prompt"

    async def run(self, user_message: str, context: Dict[str, Any] = None) -> str:
        return f"Mock response to: {user_message}"

    async def run_stream(
        self, user_message: str, context: Dict[str, Any] = None
    ) -> AsyncIterator[str]:
        yield f"Mock chunk to: {user_message}"


def test_capability_registry():
    """Verifies that the Capability Registry registers and lists metadata."""
    cap = CapabilityMetadata(
        identity="test_pnr",
        display_name="Test PNR Parser",
        description="Extracts test metrics",
        supported_intents=["pnr"],
    )
    capability_registry.register_capability(cap)
    retrieved = capability_registry.get_capability("test_pnr")
    assert retrieved is not None
    assert retrieved.display_name == "Test PNR Parser"
    assert "test_pnr" in [c.identity for c in capability_registry.list_capabilities()]


def test_dynamic_specialist_registry():
    """Verifies specialist activation, deactivation, and health tracking."""
    agent = MockTestAgent()
    agent_registry.register_versioned("mock_agent", agent, version="2.1.0")

    assert agent_registry.is_active("mock_agent") is True
    assert agent_registry.get_health("mock_agent") == "healthy"
    assert agent_registry.get_version("mock_agent") == "2.1.0"

    # Fetch agent successfully
    retrieved = agent_registry.get("mock_agent")
    assert retrieved.name == "MockTestAgent"

    # Deactivate and check error raises
    agent_registry.deactivate("mock_agent")
    assert agent_registry.is_active("mock_agent") is False
    with pytest.raises(RuntimeError):
        agent_registry.get("mock_agent")

    # Set health and retrieve
    agent_registry.set_health("mock_agent", "degraded")
    assert agent_registry.get_health("mock_agent") == "degraded"

    # Reactivate and fetch
    agent_registry.activate("mock_agent")
    assert agent_registry.is_active("mock_agent") is True
    assert agent_registry.get("mock_agent").name == "MockTestAgent"


@pytest.mark.anyio
async def test_event_bus():
    """Verifies event publishing and asynchronous subscriptions."""
    received_events = []

    async def mock_callback(event: AIEvent) -> None:
        received_events.append(event)

    event_bus.subscribe("test_event_type", mock_callback)

    event = AIEvent(
        event_type="test_event_type",
        payload={"metric": 42},
        trace_id="tr-123",
        correlation_id="corr-123",
    )
    await event_bus.publish(event)
    assert len(received_events) == 1
    assert received_events[0].payload["metric"] == 42


def test_configuration_framework():
    """Verifies that platform config updates feature flags and settings."""
    assert platform_config.is_feature_enabled("enable_cost_monitoring") is True
    platform_config.set("feature_flags", {"enable_cost_monitoring": False})
    assert platform_config.is_feature_enabled("enable_cost_monitoring") is False
    platform_config.set("feature_flags", {"enable_cost_monitoring": True})  # Restore


def test_decision_and_cost_tracing():
    """Verifies decision trace logging and cost aggregation."""
    trace = DecisionTrace(
        trace_id="trace-001",
        conversation_id="conv-001",
        user_id="user-001",
        input_message="Hello",
        routing_decision="conversation",
        confidence=0.9,
    )
    observability_framework.record_decision(trace)
    retrieved = observability_framework.get_trace("trace-001")
    assert retrieved is not None
    assert retrieved.routing_decision == "conversation"

    cost = CostTrace(
        trace_id="trace-001",
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        provider="synthetic",
        estimated_cost_usd=0.00045,
    )
    observability_framework.record_cost(cost)
    retrieved_cost = observability_framework.get_cost("trace-001")
    assert retrieved_cost is not None
    assert retrieved_cost.total_tokens == 30


def test_policy_and_governance_engine():
    """Verifies workflow policies and governance boundaries."""
    state: AIState = {
        "request_id": "req-1",
        "trace_id": "tr-1",
        "conversation_id": "conv-1",
        "user_id": "user-1",
        "message": "x" * 5000,  # Exceeds max length limit of 4096
        "intent": None,
        "selected_agent": None,
        "execution_path": [],
        "current_node": None,
        "tool_calls": [],
        "context": {"requested_provider": "unallowed_cloud"},
        "memory": [],
        "metadata": {},
        "response": "",
        "latency_ms": 0.0,
        "errors": [],
        "timestamps": {},
        "user_message": None,
        "history": None,
    }

    # Verify both length and provider eligibility policies fail
    failures = policy_engine.evaluate_all(state)
    assert "LengthLimitPolicy" in failures
    assert "ProviderEligibilityPolicy" in failures

    # Verify governance layer returns False
    assert governance_layer.verify_governance(state) is False
