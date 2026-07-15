# app/traveler/strategy/scenario_registry.py
"""
Scenario Registry (Planning §21).

Dynamically maps operational triggers to concrete action sequences.
Each scenario progresses through a deterministic lifecycle:
  Triggered → Evaluating → Active → Suppressed → Resolved
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Scenario contract
# ---------------------------------------------------------------------------


class ITravelerScenario(ABC):
    """Base contract for all traveler scenarios."""

    @abstractmethod
    def matches(self, context: Any) -> bool:
        """Return True if the scenario trigger conditions are met."""

    @abstractmethod
    def evaluate(self, context: Any) -> Dict[str, Any]:
        """Return scenario evaluation result dict."""


# ---------------------------------------------------------------------------
# Built-in scenarios (Planning §21)
# ---------------------------------------------------------------------------


class PlatformChangedScenario(ITravelerScenario):
    def matches(self, context: Any) -> bool:
        return bool(context.telemetry.get("platform_changed", False))

    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "scenario": "PLATFORM_CHANGED",
            "lifecycle": "ACTIVE",
            "action_code": "CHANGE_PLATFORM",
            "urgency": "CRITICAL",
        }


class LateArrivalScenario(ITravelerScenario):
    def matches(self, context: Any) -> bool:
        return context.telemetry.get("drift_minutes", 0.0) > 15.0

    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "scenario": "LATE_ARRIVAL",
            "lifecycle": "ACTIVE",
            "action_code": "LEAVE_EARLIER",
            "urgency": "HIGH",
        }


class TrainCancelledScenario(ITravelerScenario):
    def matches(self, context: Any) -> bool:
        return context.telemetry.get("cancelled", False)

    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "scenario": "TRAIN_CANCELLED",
            "lifecycle": "ACTIVE",
            "action_code": "BOOK_ALTERNATIVE",
            "urgency": "EMERGENCY",
        }


class TransferMissedScenario(ITravelerScenario):
    def matches(self, context: Any) -> bool:
        return context.status == "MISSED_CONNECTION"

    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "scenario": "TRANSFER_MISSED",
            "lifecycle": "ACTIVE",
            "action_code": "BOOK_ALTERNATIVE",
            "urgency": "CRITICAL",
        }


class MedicalEmergencyScenario(ITravelerScenario):
    def matches(self, context: Any) -> bool:
        return context.telemetry.get("medical_emergency", False)

    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "scenario": "MEDICAL_EMERGENCY",
            "lifecycle": "ACTIVE",
            "action_code": "EMERGENCY_STOP",
            "urgency": "EMERGENCY",
        }


class WheelchairTravelerScenario(ITravelerScenario):
    def matches(self, context: Any) -> bool:
        return context.telemetry.get("wheelchair_required", False)

    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "scenario": "WHEELCHAIR_TRAVELER",
            "lifecycle": "ACTIVE",
            "action_code": "STEP_FREE_PATH",
            "urgency": "CRITICAL",
        }


class TouristNavigationScenario(ITravelerScenario):
    def matches(self, context: Any) -> bool:
        return context.telemetry.get("tourist_mode", False)

    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "scenario": "TOURIST_NAVIGATION",
            "lifecycle": "ACTIVE",
            "action_code": "STATION_GUIDE",
            "urgency": "LOW",
        }


class FamilyTravelerScenario(ITravelerScenario):
    def matches(self, context: Any) -> bool:
        return context.telemetry.get("family_group", False)

    def evaluate(self, context: Any) -> Dict[str, Any]:
        return {
            "scenario": "FAMILY_TRAVELER",
            "lifecycle": "ACTIVE",
            "action_code": "LOWER_STRESS",
            "urgency": "MEDIUM",
        }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class ScenarioRegistry:
    """Dynamically maps triggers to concrete scenario sequences (Planning §21)."""

    def __init__(self) -> None:
        self._scenarios: List[ITravelerScenario] = []

    def register(self, scenario: ITravelerScenario) -> None:
        self._scenarios.append(scenario)

    def evaluate_all(self, context: Any) -> List[Dict[str, Any]]:
        """Return evaluation results for every matching scenario."""
        results: List[Dict[str, Any]] = []
        for scenario in self._scenarios:
            if scenario.matches(context):
                results.append(scenario.evaluate(context))
        return results

    def first_match(self, context: Any) -> Optional[Dict[str, Any]]:
        """Return evaluation for the first matching scenario, or None."""
        for scenario in self._scenarios:
            if scenario.matches(context):
                return scenario.evaluate(context)
        return None

    @classmethod
    def create_default(cls) -> "ScenarioRegistry":
        """Registers all built-in scenarios."""
        registry = cls()
        registry.register(PlatformChangedScenario())
        registry.register(LateArrivalScenario())
        registry.register(TrainCancelledScenario())
        registry.register(TransferMissedScenario())
        registry.register(MedicalEmergencyScenario())
        registry.register(WheelchairTravelerScenario())
        registry.register(TouristNavigationScenario())
        registry.register(FamilyTravelerScenario())
        return registry
