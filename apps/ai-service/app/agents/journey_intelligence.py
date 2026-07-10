import logging
from app.agents.base import BaseAgent

logger = logging.getLogger("ai-service.agents.journey_intelligence")

JOURNEY_INTELLIGENCE_PROMPT = """You are the Journey Intelligence Agent of RailYatra.
This module is a placeholder for advanced ticketing metrics, delay forecasting, alternate boarding recommendations, and fare optimization algorithms scheduled for Phase 4.

Introduce your capabilities clearly in a structured, premium way, letting the user know they are interacting with the next-generation travel engine.
"""

class JourneyIntelligenceAgent(BaseAgent):
    """
    Placeholder agent for future ticket confirmation predictions, delay predictions,
    alternate boarding recommendations, route optimization, and fare intelligence.
    """
    def __init__(self):
        super().__init__(
            name="JourneyIntelligenceAgent",
            system_prompt=JOURNEY_INTELLIGENCE_PROMPT
        )
