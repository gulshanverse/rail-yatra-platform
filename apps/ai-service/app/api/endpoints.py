import logging
import json
from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.orchestrator.graph import compiled_graph
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
    
    inputs = {
        "user_message": request.message,
        "context": combined_context,
        "history": short_term_memory.get_history(request.conversation_id)
    }

    async def event_generator():
        # Keep track of generated tokens to save to memory
        full_response = []
        classified_intent = "conversation"
        
        try:
            # Leverage LangGraph astream_events to catch classification results and stream tokens
            async for event in compiled_graph.astream_events(inputs, version="v2"):
                kind = event["event"]
                
                # Check for classification completion node
                if kind == "on_node_end" and event["name"] == "classify_node":
                    output = event["data"]["output"]
                    classified_intent = output.get("intent", "conversation")
                    yield f"data: {json.dumps({'type': 'intent', 'value': classified_intent})}\n\n"
                
                # Catch LLM tokens streaming from active agent node
                elif kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    token = chunk.content
                    if token:
                        full_response.append(token)
                        yield f"data: {json.dumps({'type': 'token', 'value': token})}\n\n"
            
            # Save Assistant message to short term sliding window
            assistant_reply = "".join(full_response)
            short_term_memory.add_message(request.conversation_id, "assistant", assistant_reply)
            
            # Save final status
            yield f"data: {json.dumps({'type': 'done', 'reply': assistant_reply})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in astream_events: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Internal orchestrator error.'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
