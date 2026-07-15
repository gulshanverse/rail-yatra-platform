# app/traveler/risk/confidence_engine.py
from typing import Any
from app.traveler.interfaces.contracts import IConfidenceEngine


class ConfidenceEngine(IConfidenceEngine):
    def calculate_confidence(self, context: Any) -> float:
        drift = context.telemetry.get("drift_minutes", 0.0)

        # Higher drift triggers lower confidence due to telemetry inaccuracies
        if drift > 30.0:
            return 0.85
        return 0.98
