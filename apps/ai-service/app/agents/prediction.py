import logging
from app.agents.base import BaseAgent
from app.prompts.prediction import PREDICTION_PROMPT

logger = logging.getLogger("ai-service.agents.prediction")


class TicketPredictionAgent(BaseAgent):
    """
    Agent responsible for analyzing delay history and waitlist levels to calculate confirmation chance.
    """

    def __init__(self):
        super().__init__(name="TicketPredictionAgent", system_prompt=PREDICTION_PROMPT)
