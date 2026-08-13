import asyncio
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.sse import format_sse
from app.memory.long_term import long_term_memory
from app.memory.short_term import short_term_memory
from app.orchestrator.workflow import workflow_executor

logger = logging.getLogger("ai-service.api.endpoints")
router = APIRouter()


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


@router.post("/chat")
async def chat(request: ChatRequest):
    """Run the LangGraph orchestrator and return a structured response."""
    conv_id = request.conversation_id or "default-session"
    user_id = request.user_id or "default-user"
    combined_context = await _build_context(request.context, conv_id, user_id)

    ai_response = await workflow_executor.execute(
        message=request.message,
        user_id=user_id,
        conversation_id=conv_id,
        context=combined_context,
    )

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
async def chat_stream(request: ChatStreamRequest):
    """Run the orchestrator and emit standards-compliant SSE events."""
    logger.info(
        f"Stream request: user={request.user_id}, conv={request.conversation_id}"
    )
    combined_context = await _build_context(
        request.context, request.conversation_id, request.user_id
    )

    async def event_generator():
        try:
            ai_response = await workflow_executor.execute(
                message=request.message,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                context=combined_context,
            )

            yield format_sse({"type": "intent", "value": ai_response.intent})

            # Preserve the canonical assistant response exactly. The SSE layer
            # only frames it; it must never mutate Markdown or provider content.
            response_text = str(ai_response.response or "")
            words = response_text.split(" ")
            for i, word in enumerate(words):
                space = " " if i > 0 else ""
                yield format_sse({"type": "token", "value": space + word})
                await asyncio.sleep(0.005)

            try:
                await short_term_memory.add_message(
                    request.conversation_id, "assistant", response_text
                )
            except Exception as ex:
                logger.warning(f"Error adding message to memory: {ex}")

            options_payload = []
            if ai_response.intent in [
                "plan_travel",
                "recommendation",
                "journey_intelligence",
                "pnr",
            ]:
                try:
                    from app.engine.models import TravelRequirement
                    from app.engine.core import journey_intelligence_engine

                    src = combined_context.get("source") or "NDLS"
                    dest = combined_context.get("destination") or "BPL"
                    j_date = combined_context.get("journey_date") or "2026-07-28"
                    pref_cls = combined_context.get("preferred_class") or "3A"
                    req = TravelRequirement(
                        source=str(src).upper(),
                        destination=str(dest).upper(),
                        journey_date=str(j_date),
                        preferred_class=str(pref_cls).upper(),
                    )
                    report = await journey_intelligence_engine.analyze_journey(req)
                    options_payload = [opt.model_dump() for opt in report.options]
                except Exception as ex:
                    logger.error(f"Error compiling stream options: {ex}")

            yield format_sse(
                {
                    "type": "done",
                    "reply": response_text,
                    "options": options_payload,
                }
            )

        except Exception:
            logger.exception("Error in chat stream event generator")
            yield format_sse(
                {"type": "error", "message": "Internal orchestrator error."}
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
