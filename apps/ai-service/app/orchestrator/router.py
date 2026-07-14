import logging
from app.orchestrator.interfaces import IRouter
from app.orchestrator.constants import (
    INTENT_TRAVEL_PLANNING,
    INTENT_PREDICTION,
    INTENT_PNR,
    INTENT_KNOWLEDGE,
    AGENT_TRAVEL_PLANNING,
    AGENT_PREDICTION,
    AGENT_PNR,
    AGENT_KNOWLEDGE,
    AGENT_CONVERSATION
)

logger = logging.getLogger("ai-service.orchestrator.router")

class Router(IRouter):
    """
    Router component that maps classified user intents to specialist agent keys.
    Returns agent keys to resolve from AgentRegistry; never instantiates agent classes itself.
    """
    async def route(self, intent: str) -> str:
        if not intent:
            logger.warning("Empty intent provided. Defaulting to conversation agent.")
            return AGENT_CONVERSATION
            
        intent_lower = intent.strip().lower()
        
        if intent_lower == INTENT_TRAVEL_PLANNING:
            return AGENT_TRAVEL_PLANNING
        elif intent_lower in [INTENT_PREDICTION, "prediction"]:
            return AGENT_PREDICTION
        elif intent_lower in [INTENT_PNR, "pnr"]:
            return AGENT_PNR
        elif intent_lower == INTENT_KNOWLEDGE:
            return AGENT_KNOWLEDGE
        else:
            # Everything else (e.g. recommendation, chit-chat, unknown intents)
            # maps to the conversation agent.
            return AGENT_CONVERSATION

router = Router()
