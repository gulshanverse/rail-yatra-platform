# app/traveler/strategy/action_engine.py
"""
Action Engine and Traveler Strategy Registry (Planning §19, §32).

The ``ActionEngine`` selects recommended actions based on telemetry context.
The ``TravelerStrategyRegistry`` provides configuration-driven strategy
look-ups for travel advisory personalisation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Strategy contract
# ---------------------------------------------------------------------------


class ITravelerStrategy(ABC):
    """Defines a pluggable traveler advisory strategy."""

    @abstractmethod
    def evaluate(self, context: Any) -> Dict[str, Any]:
        """Return an action dict for the given context."""


# ---------------------------------------------------------------------------
# Built-in strategies (Planning §19)
# ---------------------------------------------------------------------------


class SafetyFirstStrategy(ITravelerStrategy):
    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "action_code": "LEAVE_EARLIER",
            "description": "Safety buffer applied. Leave home well in advance.",
            "urgency": "HIGH",
        }


class BusinessTravelerStrategy(ITravelerStrategy):
    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "action_code": "EXPRESS_RECOVERY",
            "description": "Express recovery initiated for business schedule.",
            "urgency": "HIGH",
        }


class FamilyTravelerStrategy(ITravelerStrategy):
    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "action_code": "LOWER_STRESS",
            "description": "Compartment grouping prioritised; lower layover stress.",
            "urgency": "MEDIUM",
        }


class MedicalTravelerStrategy(ITravelerStrategy):
    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "action_code": "STEP_FREE_PATH",
            "description": "Step-free accessibility route recommended.",
            "urgency": "CRITICAL",
        }


class TouristStrategy(ITravelerStrategy):
    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "action_code": "STATION_GUIDE",
            "description": "Detailed walk navigation and station guide provided.",
            "urgency": "LOW",
        }


class MinimalWalkingStrategy(ITravelerStrategy):
    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "action_code": "SAME_PLATFORM",
            "description": "Same-platform transfers preferred; overhead bridges avoided.",
            "urgency": "MEDIUM",
        }


class FastRecoveryStrategy(ITravelerStrategy):
    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "action_code": "TATKAL_BACKUP",
            "description": "Tatkal backup options prioritised for fast recovery.",
            "urgency": "HIGH",
        }


class BudgetProtectionStrategy(ITravelerStrategy):
    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "action_code": "BUDGET_FILTER",
            "description": "Dynamic pricing offsets filtered out.",
            "urgency": "LOW",
        }


class AccessibilityStrategy(ITravelerStrategy):
    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "action_code": "WHEELCHAIR_SPACE",
            "description": "SLR layout and wheelchair spaces enforced.",
            "urgency": "CRITICAL",
        }


class LowStressStrategy(ITravelerStrategy):
    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "action_code": "SKIP_SPRINT",
            "description": "Last-minute sprint transfers bypassed.",
            "urgency": "MEDIUM",
        }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TravelerStrategyRegistry:
    """Configuration-driven strategy registry (Planning §19)."""

    def __init__(self) -> None:
        self._strategies: Dict[str, ITravelerStrategy] = {}

    def register(self, key: str, strategy: ITravelerStrategy) -> None:
        self._strategies[key] = strategy

    def get(self, key: str) -> Optional[ITravelerStrategy]:
        return self._strategies.get(key)

    def list_keys(self) -> list:
        return list(self._strategies.keys())

    @classmethod
    def create_default(cls) -> "TravelerStrategyRegistry":
        """Populates a registry with all built-in strategies."""
        registry = cls()
        registry.register("SAFETY_FIRST", SafetyFirstStrategy())
        registry.register("BUSINESS_TRAVELER", BusinessTravelerStrategy())
        registry.register("FAMILY_TRAVELER", FamilyTravelerStrategy())
        registry.register("MEDICAL_TRAVELER", MedicalTravelerStrategy())
        registry.register("TOURIST", TouristStrategy())
        registry.register("MINIMAL_WALKING", MinimalWalkingStrategy())
        registry.register("FAST_RECOVERY", FastRecoveryStrategy())
        registry.register("BUDGET_PROTECTION", BudgetProtectionStrategy())
        registry.register("ACCESSIBILITY", AccessibilityStrategy())
        registry.register("LOW_STRESS", LowStressStrategy())
        return registry


# ---------------------------------------------------------------------------
# Action Engine
# ---------------------------------------------------------------------------


class ActionEngine:
    """Catalog-driven action selector (Planning §2)."""

    def __init__(self, strategy_registry: Optional[TravelerStrategyRegistry] = None):
        self.strategy_registry = strategy_registry

    def select_action(self, context: Any) -> Any:
        drift = context.telemetry.get("drift_minutes", 0.0)
        platform_changed = context.telemetry.get("platform_changed", False)

        if platform_changed:
            return {
                "action_code": "CHANGE_PLATFORM",
                "description": "Platform changed. Proceed to Platform 4 immediately.",
                "urgency": "CRITICAL",
            }

        if drift > 30.0:
            return {
                "action_code": "LEAVE_EARLIER",
                "description": "Train delays or schedule drift detected. Leave home earlier.",
                "urgency": "HIGH",
            }

        return {
            "action_code": "WAIT",
            "description": "No immediate actions required.",
            "urgency": "LOW",
        }
