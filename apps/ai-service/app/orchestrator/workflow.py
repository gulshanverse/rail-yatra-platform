import json
import logging
import time
import uuid
from typing import Dict, Any, Optional
from app.orchestrator.interfaces import IWorkflow
from app.orchestrator.types import AIResponse
from app.orchestrator.state import AIState
from app.orchestrator.graph import get_compiled_graph
from app.orchestrator.metrics import metrics_collector
from app.orchestrator.constants import ERR_GRAPH_EXECUTION

logger = logging.getLogger("ai-service.orchestrator.workflow")


class Workflow(IWorkflow):
    """
    Core entrypoint for executing the AI platform graph orchestration layer.
    Completely decoupled from HTTP/FastAPI transport layers.
    """

    async def execute(
        self,
        message: str,
        user_id: str,
        conversation_id: str,
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> AIResponse:
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        trace_id = trace_id or f"tr-{uuid.uuid4().hex[:12]}"

        metrics_collector.increment_request()

        # 1. Initialize typed state
        state: AIState = {
            "request_id": request_id,
            "trace_id": trace_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "message": message,
            "intent": None,
            "selected_agent": None,
            "execution_path": [],
            "current_node": None,
            "tool_calls": [],
            "context": context or {},
            "memory": [],
            "metadata": {},
            "response": "",
            "latency_ms": 0.0,
            "errors": [],
            "timestamps": {"workflow_start_time": time.time()},
            "user_message": message,
            "history": [],
        }

        logger.info(
            f"[{trace_id}] Workflow execution started: user='{user_id}', conversation='{conversation_id}'"
        )

        status = "SUCCESS"
        try:
            # 2. Get and invoke the compiled LangGraph
            graph = get_compiled_graph()
            final_state = await graph.ainvoke(state)

            # Map outputs
            response_text = final_state.get("response", "")
            agent_key = final_state.get("selected_agent", "unknown")
            intent = final_state.get("intent", "conversation")
            confidence = final_state.get("context", {}).get(
                "classifier_confidence", 1.0
            )
            errors_list = final_state.get("errors", [])
            latency = final_state.get("latency_ms", 0.0)
            metadata = final_state.get("metadata", {})

            if errors_list:
                status = "DEGRADED"

        except Exception as e:
            status = "FAILED"
            metrics_collector.increment_failure()
            logger.error(
                f"[{trace_id}] Unhandled crash during graph invocation: {e}",
                exc_info=True,
            )

            # Formulate emergency fallback details
            response_text = (
                "I apologize, but I encountered a technical issue while processing your request. "
                "Please check your parameters and try again shortly."
            )
            agent_key = "unknown"
            intent = "conversation"
            confidence = 0.0
            errors_list = [f"Graph execution crashed: {str(e)}"]
            latency = (time.time() - state["timestamps"]["workflow_start_time"]) * 1000
            metadata = {
                "trace_id": trace_id,
                "request_id": request_id,
                "error_code": ERR_GRAPH_EXECUTION,
            }

        # 3. Structured JSON Logging for production log aggregation
        log_payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": "INFO" if status != "FAILED" else "ERROR",
            "logger": "ai-service.orchestrator.workflow",
            "message": "Graph execution log",
            "request_id": request_id,
            "trace_id": trace_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "intent": intent,
            "selected_agent": agent_key,
            "execution_path": state.get("execution_path", []),
            "current_node": state.get("current_node"),
            "execution_time_ms": round(latency, 2),
            "node_timings_ms": {
                k: round(v, 2) for k, v in state.get("timestamps", {}).items()
            },
            "status": status,
            "errors": errors_list,
        }

        # Write structured log message
        print(json.dumps(log_payload))

        # 4. Map final output to typed AIResponse model
        return AIResponse(
            response=response_text,
            agent=agent_key,
            intent=intent,
            confidence=confidence,
            citations=[],  # Citation structure is placeholder in M1
            latency_ms=latency,
            metadata=metadata,
            errors=errors_list,
        )


# Export default singleton workflow execution instance
workflow_executor = Workflow()
