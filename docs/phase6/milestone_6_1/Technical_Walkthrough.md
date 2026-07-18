# Milestone 6.1 Technical Walkthrough
## AI Gateway & Orchestration Foundation

This document details the code organization, node transitions, and request lifecycle flow implemented for Milestone 6.1.

---

## 1. Package Structure & Code Map
All orchestration files reside in `app/orchestrator/`:

- `interfaces.py`: Defines core abstract protocols (`IAgent`, `IRouter`, `IRegistry`, `IWorkflow`, `IGraphNode`).
- `state.py`: Strong TypedDict definition for `AIState`, ensuring type-safety across graph execution nodes.
- `types.py`: Pydantic `AIResponse` DTO carrying final outputs, citations, latencies, and correlation markers.
- `registry.py`: Dynamic thread-safe `AgentRegistry` singleton mapping agent identifiers to concrete implementations.
- `graph.py`: StateGraph compilation wrapper with lazy loading and conditional error-recovery routing.
- `nodes.py`: Node implementations (`ClassifierNode`, `RouterNode`, `AgentNode`, `MemoryNode`, `ResponseNode`, `ErrorNode`).
- `workflow.py`: Gateway controller orchestrator bridging presentation layer prompts and graph states.
- `errors.py`: Exception registry (`AIError`, `WorkflowTimeoutError`, `RoutingError`, `AgentExecutionError`) and exponential backoff retry decorators.
- `constants.py`: String key references for graph node identifiers.

---

## 2. Request Processing Flow

```
[API Entry Endpoint] ──▶ [workflow_executor]
                               │
                       1. Create AIState DTO
                               ▼
                        [get_compiled_graph()]
                               │
                       2. Graph Invocation (ainvoke)
                               ▼
                       3. Execute Node Sequence:
                            - ClassifierNode (N1)
                            - RouterNode (N2)
                            - Route Conditional Edge (E1)
                            - AgentNode / ErrorNode (N3)
                            - MemoryNode (N4)
                            - ResponseNode (N5)
                               ▼
                       4. Return AIResponse
```

---

## 3. Design Decisions
- **Lazy Graph Compilation**: Postpones compiling the LangGraph until first invocation, ensuring all agents are fully registered by the time the graph validates conditional edges.
- **Type Guard Narrowing**: Implemented `isinstance(selected, str)` checks in `route_decision` to satisfy MyPy type-safety constraints.
- **Legacy Compatibility**: Kept `user_message` and `history` optional fields inside the state payload to prevent runtime property filters in LangGraph.
