import logging
import json
import re
from typing import Dict, Any, AsyncIterator
from app.agents.base import BaseAgent
from app.engine.core import journey_intelligence_engine
from app.engine.models import TravelRequirement, UserPreferences
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger("ai-service.agents.journey_intelligence")

EXTRACTION_PROMPT = """You are an NLP extraction layer that converts travel queries into a structured JSON configuration.
Extract:
1. `source`: 3-4 letter station code (e.g. NDLS for New Delhi, BPL for Bhopal, HWH for Howrah, CSMT for Mumbai, MAS for Chennai). Default to NDLS if not specified.
2. `destination`: 3-4 letter station code (e.g. BPL, HWH, CSMT, MAS). Default to BPL if not specified.
3. `journey_date`: date in YYYY-MM-DD format. Default to 2026-07-28 if not specified.
4. `preferred_class`: SL, 3A, 2A, 1A, or CC. Default to 3A if not specified.
5. `preferences`: Multipliers (0.5 to 3.0) for:
   - `comfort` (weight comfort/AC classes)
   - `budget` (weight budget/SL classes)
   - `speed` (weight shorter journey hours)
   - `reliability` (weight punctuality & higher waitlist clearing)

Respond ONLY with a JSON object matching this structure:
{
  "source": "<source station>",
  "destination": "<destination station>",
  "journey_date": "<YYYY-MM-DD>",
  "preferred_class": "<class>",
  "preferences": {
    "comfort": 1.0,
    "budget": 1.0,
    "speed": 1.0,
    "reliability": 1.0
  }
}
Do not include markdown code blocks or additional comments.
"""

class JourneyIntelligenceAgent(BaseAgent):
    """
    Agent responsible for translating user query requests into structured parameters,
    running the Journey Intelligence Engine, and formatting decision reports.
    """
    def __init__(self):
        super().__init__(
            name="JourneyIntelligenceAgent",
            system_prompt="You are the Journey Intelligence Agent representing the decision engine."
        )

    async def _parse_query(self, user_message: str) -> TravelRequirement:
        """Uses LLM to extract structured travel parameters from unstructured text."""
        try:
            messages = [
                SystemMessage(content=EXTRACTION_PROMPT),
                HumanMessage(content=user_message)
            ]
            response = await self.llm.ainvoke(messages)
            content = str(response.content).strip()
            
            # Clean possible markdown formatting
            clean_content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE).strip()
            data = json.loads(clean_content)
            
            prefs = data.get("preferences", {})
            user_prefs = UserPreferences(
                comfort=float(prefs.get("comfort", 1.0)),
                budget=float(prefs.get("budget", 1.0)),
                speed=float(prefs.get("speed", 1.0)),
                reliability=float(prefs.get("reliability", 1.0))
            )
            
            return TravelRequirement(
                source=data.get("source", "NDLS").upper(),
                destination=data.get("destination", "BPL").upper(),
                journey_date=data.get("journey_date", "2026-07-28"),
                preferred_class=data.get("preferred_class", "3A").upper(),
                preferences=user_prefs
            )
        except Exception as e:
            logger.error(f"Failed to parse query via LLM: {e}. Using baseline fallback requirement.")
            
            # General baseline heuristics fallback
            src, dest = "NDLS", "BPL"
            msg = user_message.upper()
            if "CSMT" in msg or "MUMBAI" in msg:
                dest = "CSMT"
            if "HWH" in msg or "KOLKATA" in msg:
                src = "HWH"
            if "MAS" in msg or "CHENNAI" in msg:
                dest = "MAS"
                
            return TravelRequirement(
                source=src,
                destination=dest,
                journey_date="2026-07-28",
                preferred_class="3A",
                preferences=UserPreferences()
            )

    async def run(self, user_message: str, context: Dict[str, Any] = None) -> str:
        # 1. Parse text message
        requirement = await self._parse_query(user_message)
        
        # Override with active context parameters if present
        if context:
            if context.get("source"): requirement.source = str(context["source"])
            if context.get("destination"): requirement.destination = str(context["destination"])
            if context.get("journey_date"): requirement.journey_date = str(context["journey_date"])
            if context.get("preferred_class"): requirement.preferred_class = str(context["preferred_class"])

        # 2. Execute deterministic analysis
        report = await journey_intelligence_engine.analyze_journey(requirement)
        
        # 3. Return the compiled tradeoffs summary matrix
        return report.tradeoffs_summary

    async def run_stream(self, user_message: str, context: Dict[str, Any] = None) -> AsyncIterator[str]:
        # Stream the full report back as a single text chunk
        # Since the engine runs deterministically, we compute and stream the result.
        report_text = await self.run(user_message, context)
        # Yield words with tiny sleep to simulate streaming
        words = report_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            import asyncio
            await asyncio.sleep(0.005)
