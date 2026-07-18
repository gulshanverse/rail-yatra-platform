# app/personalization/scenarios/registry.py
import logging
from typing import Optional, Any
from app.personalization.interfaces.contracts import IScenarioRegistry
from app.personalization.dto.models import TravelerPersonalizationContext

logger = logging.getLogger(__name__)


class PersonalizationScenario:
    def __init__(self, name: str, trigger_persona: str) -> None:
        self.name = name
        self.trigger_persona = trigger_persona


class ScenarioRegistry(IScenarioRegistry):
    def __init__(self) -> None:
        self._scenarios = {
            "daily_commuter": PersonalizationScenario(
                "Daily Commuter", "WEEKLY_COMMUTER"
            ),
            "business_trip": PersonalizationScenario("Business Trip", "BUSINESS"),
            "wheelchair_traveler": PersonalizationScenario(
                "Wheelchair Traveler", "ACCESSIBILITY"
            ),
        }

    def match(self, context: TravelerPersonalizationContext) -> Optional[Any]:
        for scenario in self._scenarios.values():
            if context.persona == scenario.trigger_persona:
                logger.info("Matched scenario: %s", scenario.name)
                return scenario
        return None
