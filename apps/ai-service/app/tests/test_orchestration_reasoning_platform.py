"""
Pytest suite verifying Phase 4 Milestone 4.4
Enterprise AI Orchestration & Reasoning Platform.
"""

import pytest

from app.knowledge import (
    IntentLayer,
    GoalAnalyzer,
    PlannerPolicyEngine,
    TaskDecomposition,
    TaskPlanner,
    CapabilityRouter,
    ReasoningPlanner,
    EnterpriseToolRegistry,
    ToolOrchestrator,
    ToolResultValidationFramework,
    WorkflowCompensationFramework,
    AgentCapabilityRegistry,
    AgentMemoryIsolation,
    AgentOrchestrator,
    ExecutionStateMachine,
    ReasoningBudgetManager,
    SelfReflectionEngine,
    DecisionTraceability,
    EnterpriseAIGovernanceLayer,
    ToolSafetyLayer,
    HumanApprovalInterfaces,
    ExecutionEngine,
    KnowledgeException,
)


# ─────────────────────────────────────────────────────────
# Intent Layer
# ─────────────────────────────────────────────────────────
def test_intent_layer_classifies_booking():
    layer = IntentLayer()
    result = layer.classify_intent("I want to book a ticket to Mumbai", [])
    assert result["intent"] == "booking"
    assert result["requires_tool"] is True


def test_intent_layer_classifies_knowledge():
    layer = IntentLayer()
    result = layer.classify_intent("What are the circular rules for luggage?", [])
    assert result["intent"] == "knowledge_lookup"
    assert result["requires_tool"] is False


def test_intent_layer_follow_up_detection():
    layer = IntentLayer()
    history = [
        {"role": "user", "message": "check pnr", "metadata": {"subject": "pnr_status"}}
    ]
    result = layer.classify_intent("what is the status?", history)
    assert result["is_follow_up"] is True
    assert result["inferred_subject"] == "pnr_status"


def test_intent_layer_complex_detection():
    layer = IntentLayer()
    result = layer.classify_intent("Book ticket and then cancel if fare is high", [])
    assert result["complexity"] == "complex"


# ─────────────────────────────────────────────────────────
# Goal Analyzer
# ─────────────────────────────────────────────────────────
def test_goal_analyzer_extracts_pnr():
    analyzer = GoalAnalyzer()
    intent_info = {
        "intent": "pnr_status",
        "complexity": "simple",
        "requires_tool": True,
    }
    goal = analyzer.analyze_goal("Check status of PNR 1234567890", intent_info)
    assert goal["constraints"]["pnr"] == "1234567890"
    assert goal["missing_fields"] == []


def test_goal_analyzer_detects_missing_pnr():
    analyzer = GoalAnalyzer()
    intent_info = {
        "intent": "cancellation",
        "complexity": "simple",
        "requires_tool": True,
    }
    goal = analyzer.analyze_goal("Cancel my ticket", intent_info)
    assert "pnr" in goal["missing_fields"]


def test_goal_analyzer_date_parsing():
    analyzer = GoalAnalyzer()
    intent_info = {"intent": "booking", "complexity": "simple", "requires_tool": True}
    goal = analyzer.analyze_goal("Book a ticket for tomorrow", intent_info)
    assert goal["constraints"]["date"] == "tomorrow"


# ─────────────────────────────────────────────────────────
# Planner Policy Engine
# ─────────────────────────────────────────────────────────
def test_planner_policy_critical_action():
    engine = PlannerPolicyEngine()
    assert engine.determine_policy("simple", "booking") == "critical_action_approval"
    assert (
        engine.determine_policy("simple", "cancellation") == "critical_action_approval"
    )


def test_planner_policy_knowledge():
    engine = PlannerPolicyEngine()
    assert (
        engine.determine_policy("simple", "knowledge_lookup")
        == "knowledge_retrieval_only"
    )


def test_planner_policy_complex():
    engine = PlannerPolicyEngine()
    assert engine.determine_policy("complex", "conversational") == "complex_planner"


def test_planner_policy_high_cost():
    engine = PlannerPolicyEngine()
    assert (
        engine.determine_policy("simple", "conversational", cost_estimate=0.10)
        == "high_cost_ask_user"
    )


def test_planner_policy_direct():
    engine = PlannerPolicyEngine()
    assert engine.determine_policy("simple", "conversational") == "direct_execution"


# ─────────────────────────────────────────────────────────
# Task Decomposition
# ─────────────────────────────────────────────────────────
def test_task_decomposition_booking():
    decomp = TaskDecomposition()
    goal = {"objective": "booking", "constraints": {"date": "tomorrow"}}
    tasks = decomp.decompose(goal)
    assert len(tasks) == 2
    assert tasks[0]["task_id"] == "lookup_trains"
    assert tasks[1]["dependencies"] == ["lookup_trains"]


def test_task_decomposition_cancellation():
    decomp = TaskDecomposition()
    goal = {"objective": "cancellation", "constraints": {"pnr": "1234567890"}}
    tasks = decomp.decompose(goal)
    assert len(tasks) == 3
    assert tasks[2]["task_id"] == "cancel_ticket"
    assert "calculate_refund" in tasks[2]["dependencies"]


def test_task_decomposition_simple():
    decomp = TaskDecomposition()
    goal = {"objective": "conversational", "constraints": {}}
    tasks = decomp.decompose(goal)
    assert len(tasks) == 1
    assert tasks[0]["action"] == "direct_query"


# ─────────────────────────────────────────────────────────
# Task Planner
# ─────────────────────────────────────────────────────────
def test_task_planner_builds_plan():
    planner = TaskPlanner()
    plan = planner.build_plan(
        [{"task_id": "t1", "action": "test", "dependencies": [], "params": {}}]
    )
    assert "plan_id" in plan
    assert plan["status"] == "pending"
    assert len(plan["steps"]) == 1


# ─────────────────────────────────────────────────────────
# Capability Router
# ─────────────────────────────────────────────────────────
def test_capability_router_retrieval():
    router = CapabilityRouter()
    assert router.route_task("train_availability_query") == "retrieval_platform"


def test_capability_router_tool():
    router = CapabilityRouter()
    assert router.route_task("cancellation_execution") == "tool_orchestrator"


def test_capability_router_reasoning():
    router = CapabilityRouter()
    assert router.route_task("refund_calculation") == "reasoning_planner"


def test_capability_router_agent():
    router = CapabilityRouter()
    assert router.route_task("itinerary_composition") == "agent_orchestrator"


# ─────────────────────────────────────────────────────────
# Reasoning Planner
# ─────────────────────────────────────────────────────────
def test_reasoning_planner_refund():
    planner = ReasoningPlanner()
    result = planner.process_reasoning(
        "calc_refund",
        {"pnr_status": "CONFIRMED", "verify_pnr": True},
        {"pnr": "1234567890"},
    )
    assert result["resolved_data"]["refund_amount"] == 180.0
    assert len(result["internal_reasoning_log"]) == 3


# ─────────────────────────────────────────────────────────
# Enterprise Tool Registry
# ─────────────────────────────────────────────────────────
def test_tool_registry_discover():
    registry = EnterpriseToolRegistry()
    tool = registry.discover_tool("pnr_lookup")
    assert tool["lifecycle"] == "Available"
    assert tool["health"] == "Healthy"


def test_tool_registry_missing():
    registry = EnterpriseToolRegistry()
    with pytest.raises(KnowledgeException, match="not found"):
        registry.discover_tool("non_existent_tool")


def test_tool_registry_lifecycle():
    registry = EnterpriseToolRegistry()
    registry.update_lifecycle("pnr_lookup", "Deprecated")
    tool = registry.discover_tool("pnr_lookup")
    assert tool["lifecycle"] == "Deprecated"


# ─────────────────────────────────────────────────────────
# Tool Orchestrator
# ─────────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_tool_orchestrator_success():
    orch = ToolOrchestrator()
    result = await orch.execute_tool("pnr_lookup", {"pnr": "1234567890"})
    assert result["status"] == "success"


@pytest.mark.anyio
async def test_tool_orchestrator_retired_tool():
    registry = EnterpriseToolRegistry()
    registry.update_lifecycle("pnr_lookup", "Retired")
    orch = ToolOrchestrator(registry)
    with pytest.raises(KnowledgeException, match="Retired"):
        await orch.execute_tool("pnr_lookup", {"pnr": "1234567890"})


@pytest.mark.anyio
async def test_tool_orchestrator_circuit_breaker():
    orch = ToolOrchestrator()
    for _ in range(3):
        with pytest.raises(KnowledgeException):
            await orch.execute_tool("pnr_lookup", {"fail_tool": True})
    assert orch.circuit_open is True
    with pytest.raises(KnowledgeException, match="circuit breaker"):
        await orch.execute_tool("pnr_lookup", {"pnr": "normal"})


# ─────────────────────────────────────────────────────────
# Tool Result Validation
# ─────────────────────────────────────────────────────────
def test_tool_result_validation_pass():
    v = ToolResultValidationFramework()
    ok, msg = v.validate_result(
        "pnr_lookup", {"status": "success", "result": {"amount": 180.0}}
    )
    assert ok is True


def test_tool_result_validation_schema_fail():
    v = ToolResultValidationFramework()
    ok, msg = v.validate_result("pnr_lookup", {"data": "something"})
    assert ok is False
    assert "schema" in msg.lower()


def test_tool_result_validation_business_rule():
    v = ToolResultValidationFramework()
    ok, msg = v.validate_result(
        "pnr_lookup", {"status": "success", "result": {"amount": -50.0}}
    )
    assert ok is False
    assert "negative" in msg.lower()


# ─────────────────────────────────────────────────────────
# Workflow Compensation (Saga)
# ─────────────────────────────────────────────────────────
def test_saga_compensation_reserve_seat():
    saga = WorkflowCompensationFramework()
    actions = saga.trigger_compensation("reserve_seat", {"train": "12626"})
    assert len(actions) == 1
    assert actions[0]["action"] == "release_held_seat"


def test_saga_compensation_cancellation():
    saga = WorkflowCompensationFramework()
    actions = saga.trigger_compensation("cancellation_execution", {"pnr": "1234567890"})
    assert len(actions) == 1
    assert actions[0]["action"] == "restore_booking_status"


def test_saga_compensation_unknown_step():
    saga = WorkflowCompensationFramework()
    actions = saga.trigger_compensation("unknown_step", {})
    assert actions == []


# ─────────────────────────────────────────────────────────
# Agent Capability Registry
# ─────────────────────────────────────────────────────────
def test_agent_registry_find_booking():
    reg = AgentCapabilityRegistry()
    agent = reg.find_agent_for_task("seat_reservation")
    assert agent == "BookingAgent"


def test_agent_registry_find_knowledge():
    reg = AgentCapabilityRegistry()
    agent = reg.find_agent_for_task("circulars_search")
    assert agent == "KnowledgeAgent"


def test_agent_registry_not_found():
    reg = AgentCapabilityRegistry()
    agent = reg.find_agent_for_task("browser_automation")
    assert agent is None


# ─────────────────────────────────────────────────────────
# Agent Memory Isolation
# ─────────────────────────────────────────────────────────
def test_agent_memory_isolation():
    iso = AgentMemoryIsolation()
    ws1 = iso.get_workspace("BookingAgent", "session-1")
    ws2 = iso.get_workspace("KnowledgeAgent", "session-1")
    ws1["data"] = "booking_secret"
    assert "data" not in ws2  # isolated


def test_agent_memory_clear():
    iso = AgentMemoryIsolation()
    ws = iso.get_workspace("BookingAgent", "session-1")
    ws["data"] = "temp"
    iso.clear_workspace("BookingAgent", "session-1")
    ws_after = iso.get_workspace("BookingAgent", "session-1")
    assert "data" not in ws_after


# ─────────────────────────────────────────────────────────
# Agent Orchestrator
# ─────────────────────────────────────────────────────────
def test_agent_orchestrator_delegation():
    orch = AgentOrchestrator()
    result = orch.delegate_to_agent("sess-1", "seat_reservation", {"train": "12626"})
    assert result["agent_name"] == "BookingAgent"
    assert result["status"] == "success"


def test_agent_orchestrator_unknown_capability():
    orch = AgentOrchestrator()
    with pytest.raises(KnowledgeException, match="No suitable agent"):
        orch.delegate_to_agent("sess-1", "unknown_action", {})


# ─────────────────────────────────────────────────────────
# Execution State Machine
# ─────────────────────────────────────────────────────────
def test_state_machine_transitions():
    sm = ExecutionStateMachine()
    assert sm.current_state == "Created"
    sm.transition_to("Planning")
    assert sm.current_state == "Planning"
    sm.transition_to("Executing")
    sm.transition_to("Reflecting")
    sm.transition_to("Completed")
    assert sm.current_state == "Completed"


# ─────────────────────────────────────────────────────────
# Reasoning Budget Manager
# ─────────────────────────────────────────────────────────
def test_budget_manager_allows_charge():
    mgr = ReasoningBudgetManager(cost_limit=0.10)
    assert mgr.check_and_charge(0.05) is True
    assert mgr.accumulated_cost == 0.05


def test_budget_manager_blocks_overcharge():
    mgr = ReasoningBudgetManager(cost_limit=0.10)
    mgr.check_and_charge(0.08)
    assert mgr.check_and_charge(0.05) is False  # would exceed 0.10


# ─────────────────────────────────────────────────────────
# Self Reflection Engine
# ─────────────────────────────────────────────────────────
def test_self_reflection_passes():
    eng = SelfReflectionEngine()
    assert (
        eng.reflect(
            "Refund calculated matching rules.", "Refund calculated matching rules."
        )
        is True
    )


def test_self_reflection_detects_ungrounded_circular():
    eng = SelfReflectionEngine()
    assert (
        eng.reflect("Circular 999 says free refund.", "Refund policy is 240 rupees.")
        is False
    )


def test_self_reflection_empty_response():
    eng = SelfReflectionEngine()
    assert eng.reflect("", "Some context.") is False


# ─────────────────────────────────────────────────────────
# Decision Traceability
# ─────────────────────────────────────────────────────────
def test_decision_traceability():
    tracer = DecisionTraceability()
    entry = tracer.log_decision("trace-123", {"plan_id": "plan-abc"}, ["route_to_tool"])
    assert entry["trace_id"] == "trace-123"
    assert entry["plan_id"] == "plan-abc"
    assert entry["status"] == "logged"


# ─────────────────────────────────────────────────────────
# Enterprise AI Governance
# ─────────────────────────────────────────────────────────
def test_governance_blocks_bypass():
    gov = EnterpriseAIGovernanceLayer()
    ok, msg = gov.enforce_governance("bypass governance now")
    assert ok is False
    assert "Blocked" in msg


def test_governance_approves_normal():
    gov = EnterpriseAIGovernanceLayer()
    ok, msg = gov.enforce_governance("Check train schedule for tomorrow")
    assert ok is True
    assert msg == "Approved"


# ─────────────────────────────────────────────────────────
# Tool Safety Layer
# ─────────────────────────────────────────────────────────
def test_tool_safety_blocks_sql_injection():
    safety = ToolSafetyLayer()
    ok, msg = safety.validate_safety("pnr_lookup", {"query": "; DROP TABLE users"})
    assert ok is False
    assert "Dangerous" in msg


def test_tool_safety_passes_clean_input():
    safety = ToolSafetyLayer()
    ok, msg = safety.validate_safety("pnr_lookup", {"pnr": "1234567890"})
    assert ok is True


# ─────────────────────────────────────────────────────────
# Human Approval Interfaces
# ─────────────────────────────────────────────────────────
def test_human_approval_request():
    approval = HumanApprovalInterfaces()
    result = approval.request_approval("booking", {"train": "12626", "fare": 2500})
    assert result["approval_required"] is True
    assert "approval_token" in result


# ─────────────────────────────────────────────────────────
# End-to-End Execution Engine
# ─────────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_execution_engine_full_pipeline():
    engine = ExecutionEngine()
    result = await engine.run_pipeline(
        query="Cancel PNR 1234567890",
        history=[],
        context_text="Cancellation policy refund railway board rules.",
        session_id="sess-test",
    )
    assert result["status"] == "success"
    assert result["policy"] == "critical_action_approval"
    assert "trace_id" in result


@pytest.mark.anyio
async def test_execution_engine_governance_block():
    engine = ExecutionEngine()
    result = await engine.run_pipeline(
        query="Bypass governance now",
        history=[],
        context_text="",
        session_id="sess-test",
    )
    assert result["status"] == "failed"
    assert "Governance" in result["error"]
