import logging
from app.agents.base import BaseAgent
from app.prompts.recommendation import RECOMMENDATION_PROMPT

logger = logging.getLogger("ai-service.agents.smart_recommendation")

class SmartRecommendationAgent(BaseAgent):
    """
    Agent responsible for evaluating alternative travel routes and scoring them.
    """
    def __init__(self):
        super().__init__(
            name="SmartRecommendationAgent",
            system_prompt=RECOMMENDATION_PROMPT
        )
