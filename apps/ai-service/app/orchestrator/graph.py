import logging
from langgraph.graph import StateGraph, END
from app.orchestrator.state import AIState
from app.orchestrator.registry import agent_registry
from app.orchestrator.nodes import (
    ClassifierNode,
    RouterNode,
    AgentNode,
    MemoryNode,
    ResponseNode,
    ErrorNode,
)
from app.orchestrator.constants import (
    NODE_CLASSIFIER,
    NODE_ROUTER,
    NODE_MEMORY,
    NODE_RESPONSE,
    NODE_ERROR,
    AGENT_CONVERSATION,
)

logger = logging.getLogger("ai-service.orchestrator.graph")

# Internal compiled graph cache
_compiled_graph = None


def get_compiled_graph():
    """
    Returns the compiled StateGraph.
    Uses lazy compilation to ensure all specialist agents are registered
    before the graph nodes and conditional edges are resolved.
    """
    global _compiled_graph
    if _compiled_graph is None:
        logger.info("Initializing and compiling StateGraph lazily...")

        workflow = StateGraph(AIState)

        # 1. Register static orchestrator nodes
        workflow.add_node(NODE_CLASSIFIER, ClassifierNode())
        workflow.add_node(NODE_ROUTER, RouterNode())
        workflow.add_node(NODE_MEMORY, MemoryNode())
        workflow.add_node(NODE_RESPONSE, ResponseNode())
        workflow.add_node(NODE_ERROR, ErrorNode())

        # 2. Query AgentRegistry to add dynamic agent nodes
        # Access the private dictionary keys. Fall back to standard keys if empty during initialization.
        agent_keys = list(agent_registry._registry.keys())
        if not agent_keys:
            logger.warning("Agent registry is empty. Loading default agent keys.")
            agent_keys = [
                "travel_decision",
                "prediction",
                "pnr",
                "knowledge",
                "conversation",
            ]

        for key in agent_keys:
            # Add each agent as a dynamic node in the graph using the generic AgentNode class
            workflow.add_node(key, AgentNode(name=key))

        # 3. Define execution edges
        workflow.set_entry_point(NODE_CLASSIFIER)
        workflow.add_edge(NODE_CLASSIFIER, NODE_ROUTER)

        # 4. Define dynamic conditional routing function
        def route_decision(state: AIState) -> str:
            if state.get("errors") and not state.get("response"):
                logger.warning(
                    f"Errors detected during state processing. Routing to {NODE_ERROR}"
                )
                return NODE_ERROR

            selected = state.get("selected_agent")
            if isinstance(selected, str) and selected in agent_keys:
                return selected
            logger.warning(
                f"Selected agent '{selected}' not found. Defaulting to conversation."
            )
            return AGENT_CONVERSATION

        # Map outcomes of routing function to node identifiers
        routing_mapping = {key: key for key in agent_keys}
        routing_mapping[NODE_ERROR] = NODE_ERROR

        workflow.add_conditional_edges(NODE_ROUTER, route_decision, routing_mapping)

        # 5. Connect execution terminals to the memory placeholder
        for key in agent_keys:
            workflow.add_edge(key, NODE_MEMORY)

        # 6. Conclude standard pipeline execution
        workflow.add_edge(NODE_MEMORY, NODE_RESPONSE)
        workflow.add_edge(NODE_RESPONSE, END)

        # 7. Route error recoveries to the response node to compile latencies
        workflow.add_edge(NODE_ERROR, NODE_RESPONSE)

        _compiled_graph = workflow.compile()
        logger.info("StateGraph successfully compiled.")

    return _compiled_graph


# Export compiled_graph directly for backward compatibility
compiled_graph = get_compiled_graph()
