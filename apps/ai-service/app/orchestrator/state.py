from typing import TypedDict, Dict, Any, List, Optional


class AIState(TypedDict):
    """
    Strongly typed execution state passed between nodes in the LangGraph.
    Prevents arbitrary dictionary keys and ensures strict type checking.
    """

    request_id: str
    trace_id: str
    conversation_id: str
    user_id: str
    message: str
    intent: Optional[str]
    selected_agent: Optional[str]
    execution_path: List[str]
    current_node: Optional[str]
    tool_calls: List[Dict[str, Any]]
    context: Dict[str, Any]
    memory: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    response: str
    latency_ms: float
    errors: List[str]
    timestamps: Dict[
        str, float
    ]  # Tracks timestamps of node execution (start, end, node timings)

    # Legacy compatibility fields (prevent LangGraph from filtering them out)
    user_message: Optional[str]
    history: Optional[List[Dict[str, Any]]]
