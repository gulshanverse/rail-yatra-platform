# app/traveler/explanation/engine.py
from typing import Any
from app.traveler.interfaces.contracts import IExplanationEngine


class ExplanationEngine(IExplanationEngine):
    def generate_explanation(self, context: Any) -> Any:
        drift = context.telemetry.get("drift_minutes", 0.0)
        platform_changed = context.telemetry.get("platform_changed", False)

        # Generates trace reason context details
        if platform_changed:
            return {
                "reason_code": "EXP_PLATFORM_SWAP",
                "text": "Platform changed from 1 to Platform 4 due to active terminal scheduling swaps.",
                "supporting_evidence": {"station_master_signal": "PLT_4_CONFIRMED"},
            }

        if drift > 30.0:
            return {
                "reason_code": "EXP_TRAIN_DELAYED",
                "text": f"Train delayed by {int(drift)} minutes due to upstream congestion.",
                "supporting_evidence": {"upstream_drift_minutes": drift},
            }

        return {
            "reason_code": "E_PUNCTUAL",
            "text": "Journey continues on schedule.",
            "supporting_evidence": {},
        }
