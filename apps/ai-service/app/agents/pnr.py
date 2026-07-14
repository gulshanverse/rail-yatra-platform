import logging
from app.agents.base import BaseAgent

logger = logging.getLogger("ai-service.agents.pnr")

PNR_PROMPT = """You are the PNR Analysis Agent. Your job is to analyze booking status codes and extract passenger details and travel dates.

When checking PNR:
1. Show current station schedules and boarding details.
2. Present passenger reservation list.
3. Show waitlist position transitions (e.g. from WL 24 to WL 12).
"""


class PNRAgent(BaseAgent):
    """
    Agent responsible for checking PNR status and booking transition records.
    """

    def __init__(self):
        super().__init__(name="PNRAgent", system_prompt=PNR_PROMPT)
