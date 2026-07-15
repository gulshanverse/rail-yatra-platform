# app/traveler/risk/risk_engine.py
from typing import Any
from app.traveler.interfaces.contracts import IRiskEngine


class RiskEngine(IRiskEngine):
    def calculate_risk(self, context: Any) -> Any:
        drift = context.telemetry.get("drift_minutes", 0.0)
        connection_safety_minutes = 20.0

        # Calculate risk index float
        if drift > connection_safety_minutes:
            return {"risk_level": "HIGH", "factor": "CONNECTION_BREAK_RISK"}
        return {"risk_level": "LOW", "factor": "SAFE_LAYOVER"}
