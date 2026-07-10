import logging
from app.agents.base import BaseAgent
from app.prompts.travel import TRAVEL_PLANNER_PROMPT

logger = logging.getLogger("ai-service.agents.travel_decision")

class TravelDecisionAgent(BaseAgent):
    """
    Agent responsible for evaluating travel routes, station nodes, and scheduling connections.
    """
    def __init__(self):
        super().__init__(
            name="TravelDecisionAgent",
            system_prompt=TRAVEL_PLANNER_PROMPT
        )
