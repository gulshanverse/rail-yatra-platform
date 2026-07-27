"""
Operational Dashboard Service for Phase 8 Real-Time Operations Platform.
"""

from datetime import datetime, timezone
from app.realtime.models import DashboardMetrics
from app.realtime.store import EventStore
from app.realtime.train_tracker import TrainTracker
from app.realtime.journey_tracker import JourneyTracker
from app.realtime.incident_engine import IncidentEngine


class DashboardService:
    def __init__(
        self,
        event_store: EventStore,
        train_tracker: TrainTracker,
        journey_tracker: JourneyTracker,
        incident_engine: IncidentEngine,
    ) -> None:
        self._event_store = event_store
        self._train_tracker = train_tracker
        self._journey_tracker = journey_tracker
        self._incident_engine = incident_engine

    def get_metrics(self) -> DashboardMetrics:
        """Computes live aggregated operational metrics."""
        now_str = datetime.now(timezone.utc).isoformat()
        events_count = self._event_store.count()
        trains = self._train_tracker.get_all_states()
        journeys = self._journey_tracker.get_all_journeys()
        incidents = self._incident_engine.get_active_incidents()

        total_trains = len(trains)
        delayed_trains = sum(1 for t in trains if t.delay_minutes > 15)
        on_time_pct = (
            ((total_trains - delayed_trains) / total_trains * 100.0)
            if total_trains > 0
            else 100.0
        )

        health = "HEALTHY"
        if len(incidents) > 5:
            health = "CRITICAL"
        elif len(incidents) > 0 or delayed_trains > 0:
            health = "DEGRADED"

        return DashboardMetrics(
            total_events_processed=events_count,
            active_trains_count=total_trains,
            active_journeys_monitored=len(journeys),
            active_incidents_count=len(incidents),
            on_time_performance_percent=round(on_time_pct, 2),
            system_health_status=health,
            timestamp=now_str,
        )
