import logging
from app.orchestrator.interfaces import IRouter
from app.orchestrator.constants import (
    INTENT_TRAVEL_PLANNING,
    INTENT_PREDICTION,
    INTENT_PNR,
    INTENT_KNOWLEDGE,
    INTENT_RECOMMENDATION,
    AGENT_TRAVEL_PLANNING,
    AGENT_PREDICTION,
    AGENT_PNR,
    AGENT_KNOWLEDGE,
    AGENT_CONVERSATION,
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
        if intent_lower in {INTENT_PREDICTION, "prediction", "journey_intelligence"}:
            return AGENT_PREDICTION
        if intent_lower in {INTENT_PNR, "pnr"}:
            return AGENT_PNR
        if intent_lower == INTENT_KNOWLEDGE:
            return AGENT_KNOWLEDGE
        if intent_lower == INTENT_RECOMMENDATION:
            # Recommendations are travel decisions, not casual conversation.
            # Route them to the travel specialist so train/class/cost comparisons
            # receive domain-aware handling and structured travel data when available.
            return AGENT_TRAVEL_PLANNING
        if intent_lower == "conversation":
            return AGENT_CONVERSATION

        logger.warning("Unknown intent '%s'. Defaulting to conversation agent.", intent)
        return AGENT_CONVERSATION


router = Router()
