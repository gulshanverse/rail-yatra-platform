import logging
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional

import asyncio
from app.orchestrator.workflow import workflow_executor
from app.memory.short_term import short_term_memory
from app.memory.long_term import long_term_memory

logger = logging.getLogger("ai-service.api.endpoints")
router = APIRouter()

class ChatStreamRequest(BaseModel):
    message: str
    conversation_id: str
    user_id: str
    context: Optional[Dict[str, Any]] = None

@router.post("/chat/stream")
async def chat_stream(request: ChatStreamRequest):
    """
    Accepts user chat query, runs LangGraph orchestrator,
    and returns a Server-Sent Events stream containing classified intent and tokens.
    """
    logger.info(f"Stream request: user={request.user_id}, conv={request.conversation_id}")
    
    # Load past memory context
    redis_context = short_term_memory.get_session_context(request.conversation_id)
    db_prefs = await long_term_memory.get_user_preferences(request.user_id)
    
    # Combine context
    combined_context = {
        **(request.context or {}),
        **redis_context,
        "user_id": request.user_id,
        "preferred_class": db_prefs.get("travelPrefs", {}).get("preferred_class", "3A"),
        "seat_preference": db_prefs.get("travelPrefs", {}).get("seat_preference", "lower"),
    }
    
    
    async def event_generator():
        try:
            # 1. Execute the orchestration workflow pipeline
            ai_response = await workflow_executor.execute(
                message=request.message,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                context=combined_context
            )
            
            # 2. Yield classified intent event
            yield f"data: {json.dumps({'type': 'intent', 'value': ai_response.intent})}\n\n"
            
            # 3. Simulate streaming reply token-by-token (word-by-word) for UI compatibility
            words = ai_response.response.split(" ")
            for i, word in enumerate(words):
                space = " " if i > 0 else ""
                yield f"data: {json.dumps({'type': 'token', 'value': space + word})}\n\n"
                await asyncio.sleep(0.005)  # Responsive delay simulation
                
            # Keep short-term memory updated with the assistant response
            short_term_memory.add_message(request.conversation_id, "assistant", ai_response.response)
            
            # 4. Fetch travel choices if the query is travel/pnr related
            options_payload = []
            if ai_response.intent in ["plan_travel", "recommendation", "journey_intelligence", "pnr"]:
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
                        preferred_class=str(pref_cls).upper()
                    )
                    report = await journey_intelligence_engine.analyze_journey(req)
                    options_payload = [opt.model_dump() for opt in report.options]
                except Exception as ex:
                    logger.error(f"Error compiling stream options: {ex}")

            # 5. Yield done event
            yield f"data: {json.dumps({'type': 'done', 'reply': ai_response.response, 'options': options_payload})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in chat stream event generator: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Internal orchestrator error.'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
