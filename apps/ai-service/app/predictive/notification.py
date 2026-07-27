"""
Proactive Alert Dispatcher (FR-7, Notification Domain).
"""

import uuid
import logging
from datetime import datetime, timezone
from app.predictive.interfaces import (
    RiskEvaluation,
    PassengerProfileContext,
    ProactiveAlert,
    RiskLevel,
    DelayPrediction,
)

logger = logging.getLogger("ai-service.predictive.notification")


class ProactiveAlertDispatcher:
    """
    Proactive Alert Generation and Dispatching Engine (FR-7).
    """

    async def evaluate_and_dispatch_alert(
        self,
        risk: RiskEvaluation,
        delay: DelayPrediction,
        passenger: PassengerProfileContext,
    ) -> ProactiveAlert | None:
        alert_needed = False
        alert_type = "NONE"
        severity = RiskLevel.LOW
        message = ""
        action = None

        if risk.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            alert_needed = True
            alert_type = "CONNECTION_RISK_WARNING"
            severity = risk.risk_level
            message = (
                f"Warning: Your connection at {risk.connecting_train_number or 'transfer station'} "
                f"has a {risk.missed_connection_probability}% risk of failure due to expected {delay.predicted_delay_mins} min delay."
            )
            action = "Switch to recommended Rajdhani fallback train to preserve your journey schedule."

        elif delay.predicted_delay_mins >= 45:
            alert_needed = True
            alert_type = "SIGNIFICANT_DELAY_ALERT"
            severity = RiskLevel.MEDIUM
            message = f"Notice: Train {delay.train_number} is projected to arrive {delay.predicted_delay_mins} minutes late at {delay.station_code}."
            action = "Adjust your platform pickup or station arrival plans."

        if not alert_needed:
            return None

        alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.now(timezone.utc).isoformat()

        logger.info(f"Dispatched Proactive Alert {alert_id} ({alert_type}) to traveler {passenger.traveler_id}")

        return ProactiveAlert(
            alert_id=alert_id,
            traveler_id=passenger.traveler_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            actionable_recommendation=action,
            dispatched_at=now_str,
        )
