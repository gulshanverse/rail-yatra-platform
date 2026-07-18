# app/personalization/strategies/registry.py
import logging
from typing import List, Any, Dict
from app.personalization.interfaces.contracts import IStrategyRegistry
from app.personalization.dto.models import TravelerPersonalizationContext

logger = logging.getLogger(__name__)


class ComfortFirstStrategy:
    def apply(self, context: TravelerPersonalizationContext) -> Dict[str, Any]:
        return {"comfort_upgrade": True}


class AccessibilityStrategy:
    def apply(self, context: TravelerPersonalizationContext) -> Dict[str, Any]:
        return {"step_free_access": True}


class BusinessTravelerStrategy:
    def apply(self, context: TravelerPersonalizationContext) -> Dict[str, Any]:
        return {"fast_transit": True}


class StrategyRegistry(IStrategyRegistry):
    def __init__(self) -> None:
        self._strategies: Dict[str, Any] = {}
        self.register("ComfortFirstStrategy", ComfortFirstStrategy())
        self.register("AccessibilityStrategy", AccessibilityStrategy())
        self.register("BusinessTravelerStrategy", BusinessTravelerStrategy())

    def select(self, context: TravelerPersonalizationContext) -> List[Any]:
        selected = []
        if context.persona == "WEEKLY_COMMUTER" or context.persona == "BUSINESS":
            selected.append(self._strategies.get("BusinessTravelerStrategy"))
        if (
            context.explicit_preferences.get("accessibility")
            or context.persona == "ACCESSIBILITY"
        ):
            selected.append(self._strategies.get("AccessibilityStrategy"))

        if not selected:
            selected.append(self._strategies.get("ComfortFirstStrategy"))
        return selected

    def register(self, name: str, strategy: Any) -> None:
        self._strategies[name] = strategy
        logger.info("Registered strategy: %s", name)
