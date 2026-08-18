import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.sse import format_sse
from app.memory.long_term import long_term_memory
from app.memory.short_term import short_term_memory
from app.orchestrator.workflow import workflow_executor

logger = logging.getLogger("ai-service.api.endpoints")
router = APIRouter()

WORKFLOW_TIMEOUT_SECONDS = 45
HEARTBEAT_SECONDS = 8


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = "default-session"
    user_id: Optional[str] = "default-user"
    context: Optional[Dict[str, Any]] = None


class ChatStreamRequest(BaseModel):
    message: str
    conversation_id: str
    user_id: str
    context: Optional[Dict[str, Any]] = None


async def _build_context(
    request_context: Optional[Dict[str, Any]], conversation_id: str, user_id: str
) -> dict:
    redis_context = {}
    try:
        redis_context = await short_term_memory.get_session_context(conversation_id)
    except Exception as e:
        logger.warning(f"Failed to fetch short term memory context: {e}")

    db_prefs = {}
    try:
        db_prefs = (await long_term_memory.get_user_preferences(user_id)) or {}
    except Exception as e:
        logger.warning(f"Failed to fetch user preferences: {e}")

    travel_prefs = db_prefs.get("travelPrefs") or {}
    return {
        **(request_context or {}),
        **redis_context,
        "user_id": user_id,
        "preferred_class": travel_prefs.get("preferred_class", "3A"),
        "seat_preference": travel_prefs.get("seat_preference", "lower"),
    }


async def _execute_workflow(request: ChatRequest | ChatStreamRequest, context: dict):
    """Execute the AI graph with a hard upper bound so provider outages cannot hang chat."""
    return await asyncio.wait_for(
        workflow_executor.execute(
            message=request.message,
            user_id=request.user_id or "default-user",
            conversation_id=request.conversation_id or "default-session",
            context=context,
        ),
        timeout=WORKFLOW_TIMEOUT_SECONDS,
    )


def _classify_ai_error(error: Exception) -> tuple[str, str]:
    text = str(error).lower()
    if isinstance(error, asyncio.TimeoutError):
        return "AI_WORKFLOW_TIMEOUT", "The AI service took too long to respond. Please try again in a moment."
    if any(term in text for term in ("429", "rate limit", "quota", "resource exhausted")):
        return "AI_PROVIDER_RATE_LIMIT", "The AI provider is temporarily rate-limited. Please try again shortly."
    if any(term in text for term in ("401", "403", "api key", "authentication", "unauthorized")):
        return "AI_PROVIDER_CONFIGURATION", "The AI provider configuration is unavailable."
    if any(term in text for term in ("timeout", "timed out", "deadline")):
        return "AI_PROVIDER_TIMEOUT", "The AI provider timed out. Please try again shortly."
    return "AI_WORKFLOW_ERROR", "The AI workflow could not complete this request. Please try again."


def _event_factory(correlation_id: str):
    sequence = 0

    def make_event(event_type: str, **payload: Any) -> tuple[dict[str, Any], str]:
        nonlocal sequence
        sequence += 1
        event_id = f"{correlation_id}:{sequence}"
        return (
            {
                "type": event_type,
                "event_id": event_id,
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **payload,
            },
            event_id,
        )

    return make_event


@router.post("/chat")
async def chat(request: ChatRequest):
    """Run the LangGraph orchestrator and return a structured response."""
    conv_id = request.conversation_id or "default-session"
    user_id = request.user_id or "default-user"
    combined_context = await _build_context(request.context, conv_id, user_id)

    try:
        ai_response = await _execute_workflow(request, combined_context)
    except Exception as error:
        code, message = _classify_ai_error(error)
        logger.exception("AI workflow failed: code=%s user=%s conversation=%s", code, user_id, conv_id)
        return {
            "reply": message,
            "parsed_intent": "conversation",
            "confidence": 0.0,
            "explanation": "AI workflow failure",
            "credits_left": 100,
            "agent": "error-handler",
            "metadata": {"error_code": code},
        }

    try:
        await short_term_memory.add_message(conv_id, "assistant", ai_response.response)
    except Exception as e:
        logger.warning(f"Failed to save message to short term memory: {e}")

    return {
        "reply": ai_response.response,
        "parsed_intent": ai_response.intent,
        "confidence": ai_response.confidence,
        "explanation": f"Orchestrated by {ai_response.agent} agent.",
        "credits_left": 100,
        "agent": ai_response.agent,
        "metadata": ai_response.metadata,
    }


@router.post("/chat/stream")
async def chat_stream(request: ChatStreamRequest, http_request: Request):
    """Run the orchestrator and emit a resilient, structured SSE event stream."""
    correlation_id = uuid4().hex
    logger.info("Stream request: user=%s, conv=%s, correlation=%s", request.user_id, request.conversation_id, correlation_id)
    combined_context = await _build_context(request.context, request.conversation_id, request.user_id)
    make_event = _event_factory(correlation_id)

    async def event_generator():
        workflow_task: asyncio.Task[Any] | None = None
        try:
            for event_type, payload in [
                ("status", {"value": "processing"}),
                ("thinking", {"stage": "understanding", "label": "Understanding your request", "state": "active"}),
                ("tool_start", {"tool": "journey_intelligence", "label": "Preparing railway signals"}),
            ]:
                event, event_id = make_event(event_type, **payload)
                yield format_sse(event, event_id=event_id)

            workflow_task = asyncio.create_task(_execute_workflow(request, combined_context))
            while not workflow_task.done():
                if await http_request.is_disconnected():
                    workflow_task.cancel()
                    await asyncio.gather(workflow_task, return_exceptions=True)
                    logger.info("Client disconnected from AI stream correlation=%s", correlation_id)
                    return
                try:
                    await asyncio.wait_for(asyncio.shield(workflow_task), timeout=HEARTBEAT_SECONDS)
                except asyncio.TimeoutError:
                    heartbeat, event_id = make_event("heartbeat", value="alive")
                    yield format_sse(heartbeat, event_id=event_id)

            try:
                ai_response = await workflow_task
            except Exception as error:
                code, message = _classify_ai_error(error)
                logger.exception("AI stream workflow failed: code=%s correlation=%s", code, correlation_id)
                event, event_id = make_event("error", code=code, message=message, retryable=code != "AI_PROVIDER_CONFIGURATION")
                yield format_sse(event, event_id=event_id)
                done, done_id = make_event("done", status="error")
                yield format_sse(done, event_id=done_id)
                return

            for payload in [
                {"stage": "understanding", "label": "Understanding your request", "state": "complete"},
                {"stage": "searching", "label": "Searching trains", "state": "complete"},
                {"stage": "availability", "label": "Checking availability", "state": "complete"},
                {"stage": "reliability", "label": "Comparing reliability", "state": "active"},
            ]:
                event, event_id = make_event("thinking", **payload)
                yield format_sse(event, event_id=event_id)

            intent_event, intent_id = make_event("intent", value=ai_response.intent, confidence=ai_response.confidence)
            yield format_sse(intent_event, event_id=intent_id)
            tool_complete, tool_complete_id = make_event("tool_complete", tool="journey_intelligence", label="Railway signals ready")
            yield format_sse(tool_complete, event_id=tool_complete_id)

            response_text = str(ai_response.response or "").strip()
            if not response_text:
                error_event, error_id = make_event("error", message="The AI service returned an empty response. Please try again.", code="EMPTY_AI_RESPONSE", retryable=True)
                yield format_sse(error_event, event_id=error_id)
                done_event, done_id = make_event("done", status="error")
                yield format_sse(done_event, event_id=done_id)
                return

            for i, word in enumerate(response_text.split(" ")):
                space = " " if i > 0 else ""
                token_event, token_id = make_event("token", value=space + word)
                yield format_sse(token_event, event_id=token_id)
                await asyncio.sleep(0.005)

            try:
                await short_term_memory.add_message(request.conversation_id, "assistant", response_text)
            except Exception as ex:
                logger.warning(f"Error adding message to memory: {ex}")

            options_payload = []
            if ai_response.intent in ["plan_travel", "recommendation", "journey_intelligence", "pnr"]:
                try:
                    from app.engine.models import TravelRequirement
                    from app.engine.core import journey_intelligence_engine

                    src = combined_context.get("source") or "NDLS"
                    dest = combined_context.get("destination") or "BPL"
                    j_date = combined_context.get("journey_date") or "2026-07-28"
                    pref_cls = combined_context.get("preferred_class") or "3A"
                    req = TravelRequirement(source=str(src).upper(), destination=str(dest).upper(), journey_date=str(j_date), preferred_class=str(pref_cls).upper())
                    report = await journey_intelligence_engine.analyze_journey(req)
                    options_payload = [opt.model_dump() for opt in report.options]
                except Exception as ex:
                    logger.error(f"Error compiling stream options: {ex}")

            if options_payload:
                recommendation, recommendation_id = make_event("recommendation", options=options_payload, label="Best options for your journey")
                yield format_sse(recommendation, event_id=recommendation_id)
                result, result_id = make_event("train_results", options=options_payload)
                yield format_sse(result, event_id=result_id)

            message_event, message_id = make_event("message", message=response_text)
            yield format_sse(message_event, event_id=message_id)
            done_event, done_id = make_event("done", reply=response_text, options=options_payload, status="complete")
            yield format_sse(done_event, event_id=done_id)

        except asyncio.CancelledError:
            if workflow_task and not workflow_task.done():
                workflow_task.cancel()
            raise
        except Exception as error:
            code, message = _classify_ai_error(error)
            logger.exception("Unhandled chat stream failure: code=%s correlation=%s", code, correlation_id)
            event, event_id = make_event("error", code=code, message=message, retryable=True)
            yield format_sse(event, event_id=event_id)
            done, done_id = make_event("done", status="error")
            yield format_sse(done, event_id=done_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-RailYatra-Correlation-Id": correlation_id,
        },
    )
