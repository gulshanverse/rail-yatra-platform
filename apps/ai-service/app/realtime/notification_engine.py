"""
Prioritized Notification Engine for Phase 8 Real-Time Operations Platform.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict
from app.realtime.interfaces import IncidentSeverity, NotificationPriority
from app.realtime.models import Incident, JourneyState, NotificationPayload


class NotificationEngine:
    def __init__(self) -> None:
        self._history: Dict[str, NotificationPayload] = {}

    def orchestrate_notification(
        self, journey: JourneyState, incident: Incident, custom_message: str = ""
    ) -> NotificationPayload:
        """Prioritizes and creates a notification payload for an impacted passenger."""
        now_str = datetime.now(timezone.utc).isoformat()
        priority = NotificationPriority.MEDIUM

        if incident.severity == IncidentSeverity.CRITICAL:
            priority = NotificationPriority.URGENT
        elif incident.severity == IncidentSeverity.HIGH:
            priority = NotificationPriority.HIGH
        elif incident.severity == IncidentSeverity.LOW:
            priority = NotificationPriority.LOW

        msg = custom_message or f"{incident.title}: {incident.description}"

        notification = NotificationPayload(
            notification_id=f"notif-{uuid.uuid4().hex[:10]}",
            journey_id=journey.journey_id,
            passenger_id=journey.passenger_id,
            title=f"Travel Advisory - Train {journey.train_number}",
            message=msg,
            priority=priority,
            dispatched_at=now_str,
        )

        self._history[notification.notification_id] = notification
        return notification

    def get_history(self) -> List[NotificationPayload]:
        """Returns full notification dispatch history."""
        return list(self._history.values())

    def get_notifications_by_journey(self, journey_id: str) -> List[NotificationPayload]:
        """Returns dispatched notifications for a specific journey."""
        return [n for n in self._history.values() if n.journey_id == journey_id]
