import logging
import time
from app.orchestrator.state import AIState
from app.orchestrator.registry import agent_registry
from app.orchestrator.classifier import intent_classifier
from app.orchestrator.router import router
from app.orchestrator.metrics import metrics_collector
from app.orchestrator.errors import AgentExecutionError
from app.orchestrator.constants import (
    NODE_CLASSIFIER,
    NODE_ROUTER,
    NODE_AGENT,
    NODE_MEMORY,
    NODE_RESPONSE,
    NODE_ERROR,
    AGENT_CONVERSATION,
)

logger = logging.getLogger("ai-service.orchestrator.nodes")


class BaseNode:
    """Base class for all graph nodes providing timing and tracing helpers."""

    def __init__(self, name: str):
        self.name = name

    def _start_timing(self, state: AIState) -> float:
        # Support both new state schema and legacy inputs gracefully
        if "execution_path" not in state:
            state["execution_path"] = []
        if "timestamps" not in state:
            state["timestamps"] = {}
        if "trace_id" not in state:
            state["trace_id"] = "legacy-trace"
        if "request_id" not in state:
            state["request_id"] = "legacy-req"
        if "errors" not in state:
            state["errors"] = []
        if "context" not in state:
            state["context"] = {}
        if "metadata" not in state:
            state["metadata"] = {}
        if "response" not in state:
            state["response"] = ""
        if "message" not in state and "user_message" in state:
            state["message"] = state["user_message"]
        if "user_message" not in state and "message" in state:
            state["user_message"] = state["message"]

        state["current_node"] = self.name
        state["execution_path"].append(self.name)
        return time.time()

    def _end_timing(self, state: AIState, start_time: float) -> None:
        latency_ms = (time.time() - start_time) * 1000
        state["timestamps"][self.name] = latency_ms
        metrics_collector.record_node_latency(self.name, latency_ms)


class ClassifierNode(BaseNode):
    """
    Classifies the user message intent.
    Utilizes intent_classifier from classifier.py.
    """

    def __init__(self):
        super().__init__(NODE_CLASSIFIER)

    async def __call__(self, state: AIState) -> AIState:
        start_time = self._start_timing(state)
        logger.info(f"[{state['trace_id']}] Entering ClassifierNode")

        try:
            res = await intent_classifier.classify(state["message"])
            state["intent"] = res.get("intent", "conversation")
            # Preserve classifier details in context
            state["context"]["classifier_confidence"] = res.get("confidence", 0.5)
            state["context"]["classifier_reason"] = res.get("reason", "")
        except Exception as e:
            logger.error(f"[{state['trace_id']}] Error in intent classification: {e}")
            state["errors"].append(f"Classification failed: {str(e)}")
            # Fallback intent
            state["intent"] = "conversation"
            state["context"]["classifier_confidence"] = 0.0
            state["context"]["classifier_reason"] = f"Error fallback: {str(e)}"

        self._end_timing(state, start_time)
        return state


class RouterNode(BaseNode):
    """
    Routes the execution path to the designated specialist agent.
    Decoupled from concrete agents via AgentRegistry lookup identifiers.
    """

    def __init__(self):
        super().__init__(NODE_ROUTER)

    async def __call__(self, state: AIState) -> AIState:
        start_time = self._start_timing(state)
        logger.info(f"[{state['trace_id']}] Entering RouterNode")

        intent = state.get("intent") or "conversation"

        try:
            # Delegate routing decision to Router component
            agent_key = await router.route(intent)
            state["selected_agent"] = agent_key
            logger.info(
                f"[{state['trace_id']}] Routed intent '{intent}' to agent key '{agent_key}'"
            )
        except Exception as e:
            logger.error(f"[{state['trace_id']}] Routing failed: {e}")
            state["errors"].append(f"Routing failed: {str(e)}")
            state["selected_agent"] = AGENT_CONVERSATION

        self._end_timing(state, start_time)
        return state


class AgentNode(BaseNode):
    """
    Dynamically resolves and executes the active agent from the registry.
    """

    def __init__(self, name: str = NODE_AGENT):
        super().__init__(name)

    async def __call__(self, state: AIState) -> AIState:
        start_time = self._start_timing(state)
        logger.info(f"[{state['trace_id']}] Entering AgentNode")

        agent_key = state.get("selected_agent") or AGENT_CONVERSATION

        try:
            # Dynamically fetch the specialist agent from the registry
            agent = agent_registry.get(agent_key)
            metrics_collector.record_agent_execution(agent_key)

            logger.info(
                f"[{state['trace_id']}] Executing specialist agent: '{agent.name}'"
            )

            # Execute the agent
            response = await agent.run(state["message"], state["context"])
            state["response"] = response
        except Exception as e:
            logger.error(
                f"[{state['trace_id']}] Error in agent execution '{agent_key}': {e}"
            )
            state["errors"].append(f"Agent execution failed: {str(e)}")
            raise AgentExecutionError(f"Failed to run agent '{agent_key}': {str(e)}")

        self._end_timing(state, start_time)
        return state


class MemoryNode(BaseNode):
    """
    Placeholder Node for Short Term and Long Term Memory syncing.
    No active database or caching operations are performed here in Milestone 1.
    """

    def __init__(self):
        super().__init__(NODE_MEMORY)

    async def __call__(self, state: AIState) -> AIState:
        start_time = self._start_timing(state)
        logger.info(
            f"[{state['trace_id']}] Entering MemoryNode to save interaction context"
        )

        from app.memory.short_term import memory_manager

        user_id = state.get("user_id")
        session_id = state.get("conversation_id")
        user_message = state.get("message")
        agent_response = state.get("response")

        if user_id and session_id and user_message and agent_response:
            try:
                await memory_manager.save_interaction(
                    user_id=user_id,
                    session_id=session_id,
                    user_message=user_message,
                    agent_response=agent_response,
                    metadata=state.get("metadata"),
                )
                logger.info(
                    f"[{state['trace_id']}] Interaction successfully saved to memory manager."
                )
            except Exception as e:
                logger.error(
                    f"[{state['trace_id']}] Error saving interaction to memory manager: {e}"
                )
                state["errors"].append(f"Memory save error: {str(e)}")

        self._end_timing(state, start_time)
        return state


class ResponseNode(BaseNode):
    """
    Prepares the final structured metadata and execution summary.
    """

    def __init__(self):
        super().__init__(NODE_RESPONSE)

    async def __call__(self, state: AIState) -> AIState:
        start_time = self._start_timing(state)
        logger.info(f"[{state['trace_id']}] Entering ResponseNode")

        state["current_node"] = None

        # Track overall latency
        overall_start = state["timestamps"].get("workflow_start_time", time.time())
        latency_ms = (time.time() - overall_start) * 1000
        state["latency_ms"] = latency_ms
        metrics_collector.record_request_latency(latency_ms)

        # Update metadata summary
        state["metadata"].update(
            {
                "trace_id": state["trace_id"],
                "request_id": state["request_id"],
                "execution_path": state["execution_path"],
                "node_timings_ms": state["timestamps"],
            }
        )

        logger.info(
            f"[{state['trace_id']}] Orchestrator execution successful. Latency: {latency_ms:.2f}ms"
        )

        self._end_timing(state, start_time)
        return state


class ErrorNode(BaseNode):
    """
    Node invoked when errors are detected.
    Injects fallback messages and captures error diagnostics.
    """

    def __init__(self):
        super().__init__(NODE_ERROR)

    async def __call__(self, state: AIState) -> AIState:
        start_time = self._start_timing(state)
        logger.warning(
            f"[{state['trace_id']}] Entering ErrorNode due to execution issues."
        )

        metrics_collector.increment_failure()

        if not state["response"]:
            # Standard graceful fallback response
            state["response"] = (
                "I apologize, but I encountered a technical issue while processing your request. "
                "Please check your travel parameters or PNR number and try again shortly."
            )

        state["current_node"] = None

        # Track overall latency
        overall_start = state["timestamps"].get("workflow_start_time", time.time())
        state["latency_ms"] = (time.time() - overall_start) * 1000

        self._end_timing(state, start_time)
        return state
