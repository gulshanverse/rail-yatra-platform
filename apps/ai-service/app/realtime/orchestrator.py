"""
Central Orchestrator for Phase 8 Real-Time Operations Platform.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.realtime.models import (
    OperationalEvent,
    TrainState,
    JourneyState,
    ETAResult,
    DashboardMetrics,
    RealTimeAIContext,
)
from app.realtime.gateway import RealTimeEventGateway
from app.realtime.dispatcher import EventDispatcher
from app.realtime.store import EventStore
from app.realtime.train_tracker import TrainTracker
from app.realtime.journey_tracker import JourneyTracker
from app.realtime.eta_engine import ETAEngine
from app.realtime.incident_engine import IncidentEngine
from app.realtime.decision_engine import DecisionEngine
from app.realtime.notification_engine import NotificationEngine
from app.realtime.dashboard_service import DashboardService
from app.realtime.observability import RealTimeObservability


class RealTimeOperationsOrchestrator:
    def __init__(self) -> None:
        self.gateway = RealTimeEventGateway()
        self.dispatcher = EventDispatcher()
        self.store = EventStore()
        self.train_tracker = TrainTracker()
        self.journey_tracker = JourneyTracker()
        self.eta_engine = ETAEngine()
        self.incident_engine = IncidentEngine()
        self.decision_engine = DecisionEngine()
        self.notification_engine = NotificationEngine()
        self.observability = RealTimeObservability()
        self.dashboard_service = DashboardService(
            event_store=self.store,
            train_tracker=self.train_tracker,
            journey_tracker=self.journey_tracker,
            incident_engine=self.incident_engine,
        )
        self._setup_event_subscriptions()

    def _setup_event_subscriptions(self) -> None:
        """Subscribes core engine state updates to the event dispatcher."""
        self.dispatcher.subscribe_all(self._on_event_dispatched)

    async def _on_event_dispatched(self, event: OperationalEvent) -> None:
        """Internal handler executing the standard operational event lifecycle."""
        # 1. Update Train State
        train_state = self.train_tracker.update_state(event)

        # 2. Update Impacted Passenger Journeys
        impacted_journeys = self.journey_tracker.get_journeys_by_train(event.train_number)
        updated_journeys: List[JourneyState] = []
        for j in impacted_journeys:
            upd = self.journey_tracker.update_journey_with_event(
                journey_id=j.journey_id, event=event, train_state=train_state
            )
            if upd:
                updated_journeys.append(upd)

        # 3. Evaluate Incident Engine
        new_incidents = self.incident_engine.evaluate_event_for_incidents(
            event=event, train_state=train_state, affected_journeys=updated_journeys
        )

        # 4. Generate Recommendations & Dispatch Notifications for Critical Incidents
        for inc in new_incidents:
            self.observability.record_incident_detected()
            for j in updated_journeys:
                recs = self.decision_engine.generate_recommendations(
                    incident=inc, journey_state=j
                )
                rec_msg = " ".join(recs)
                self.notification_engine.orchestrate_notification(
                    journey=j, incident=inc, custom_message=rec_msg
                )
                self.observability.record_notification_dispatched()

    async def process_raw_event(self, raw_data: Dict[str, Any]) -> OperationalEvent:
        """Main entry point: Ingests, validates, stores, and dispatches a raw operational event."""
        with self.observability.record_latency():
            event = self.gateway.validate_and_normalize(raw_data)
            self.store.append(event)
            self.observability.record_event_ingested()
            await self.dispatcher.dispatch(event)
            return event

    def register_passenger_journey(
        self,
        journey_id: str,
        passenger_id: str,
        train_number: str,
        origin_station: str,
        destination_station: str,
        scheduled_eta: str,
    ) -> JourneyState:
        """Registers a passenger journey for active real-time monitoring."""
        return self.journey_tracker.register_journey(
            journey_id=journey_id,
            passenger_id=passenger_id,
            train_number=train_number,
            origin_station=origin_station,
            destination_station=destination_station,
            scheduled_eta=scheduled_eta,
        )

    def get_train_state(self, train_number: str) -> Optional[TrainState]:
        """Returns current train state."""
        return self.train_tracker.get_state(train_number)

    def get_journey_state(self, journey_id: str) -> Optional[JourneyState]:
        """Returns current passenger journey state."""
        return self.journey_tracker.get_journey(journey_id)

    def calculate_dynamic_eta(
        self, train_number: str, target_station: str, scheduled_arrival_iso: str
    ) -> ETAResult:
        """Calculates dynamic ETA for a train at a specific station."""
        train_state = self.train_tracker.get_state(train_number)
        if not train_state:
            now_str = datetime.now(timezone.utc).isoformat()
            train_state = TrainState(
                train_number=train_number,
                current_station="UNKNOWN",
                status="SCHEDULED",
                delay_minutes=0,
                last_updated=now_str,
            )
        return self.eta_engine.calculate_eta(
            train_state=train_state,
            target_station=target_station,
            scheduled_arrival_iso=scheduled_arrival_iso,
        )

    def get_dashboard_metrics(self) -> DashboardMetrics:
        """Returns live control room dashboard metrics."""
        return self.dashboard_service.get_metrics()

    def get_live_ai_context(
        self, train_number: str, journey_id: Optional[str] = None
    ) -> RealTimeAIContext:
        """Generates live operational context for AI Core and conversation agents."""
        t_state = self.train_tracker.get_state(train_number)
        j_state = self.journey_tracker.get_journey(journey_id) if journey_id else None
        active_incidents = [
            inc
            for inc in self.incident_engine.get_active_incidents()
            if inc.train_number == train_number
        ]

        dynamic_eta = None
        if t_state:
            dynamic_eta = self.eta_engine.calculate_eta(
                train_state=t_state,
                target_station=t_state.next_station or t_state.current_station,
                scheduled_arrival_iso=t_state.last_updated,
            )

        recs: List[str] = []
        if active_incidents and j_state:
            recs = self.decision_engine.generate_recommendations(
                incident=active_incidents[0], journey_state=j_state
            )

        return RealTimeAIContext(
            train_number=train_number,
            journey_id=journey_id,
            live_train_state=t_state,
            active_journey_state=j_state,
            active_incidents=active_incidents,
            dynamic_eta=dynamic_eta,
            ai_recommendations=recs,
        )
