# app/traveler/alerts/alert_engine.py
from typing import Any, List
from app.traveler.interfaces.contracts import IAlertEngine
from app.traveler.dto.models import TravelerAlertDTO


class AlertEngine(IAlertEngine):
    def evaluate_alerts(self, context: Any) -> List[TravelerAlertDTO]:
        alerts = []
        drift = context.telemetry.get("drift_minutes", 0.0)

        # Enforces deduplication rule matching: only delay deltas > 10m fire alerts
        if drift > 10.0:
            alerts.append(
                TravelerAlertDTO(
                    alert_id="alt_delay_01",
                    priority="HIGH",
                    title="Train Delay Warning",
                    body=f"Your train is currently running {int(drift)} minutes late.",
                    geofence_radius_meters=1000,
                )
            )

        platform_changed = context.telemetry.get("platform_changed", False)
        if platform_changed:
            alerts.append(
                TravelerAlertDTO(
                    alert_id="alt_plt_change",
                    priority="CRITICAL",
                    title="Platform Swap Alert",
                    body="Platform changed to Platform 4.",
                    geofence_radius_meters=500,
                )
            )

        return alerts
