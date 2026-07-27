"""
Comprehensive Test Suite for Phase 8 Real-Time Operations Platform.

Covers:
- Event Gateway validation & normalization
- Event Store persistence
- Event Dispatcher pub/sub routing
- Train State Machine transitions
- Journey State Machine lifecycle
- Dynamic ETA Engine calculations
- Incident Detection Engine evaluation
- Decision Engine recommendations
- Notification Engine orchestration
- Dashboard Service metrics aggregation
- Observability telemetry counters
- Orchestrator end-to-end workflow
- REST API endpoints (FastAPI TestClient)
"""

import pytest
from fastapi.testclient import TestClient

# ──────────────────────────────────────────────────────────────────────────────
# Domain Model Imports
# ──────────────────────────────────────────────────────────────────────────────
from app.realtime.interfaces import (
    EventType,
    TrainStatus,
    JourneyStatus,
    IncidentSeverity,
    NotificationPriority,
)
from app.realtime.models import (
    OperationalEvent,
    TrainState,
    JourneyState,
    Incident,
    ETAResult,
    NotificationPayload,
    DashboardMetrics,
    RealTimeAIContext,
)
from app.realtime.events import EventFactory
from app.realtime.gateway import RealTimeEventGateway
from app.realtime.store import EventStore
from app.realtime.dispatcher import EventDispatcher
from app.realtime.train_tracker import TrainTracker
from app.realtime.journey_tracker import JourneyTracker
from app.realtime.eta_engine import ETAEngine
from app.realtime.incident_engine import IncidentEngine
from app.realtime.decision_engine import DecisionEngine
from app.realtime.notification_engine import NotificationEngine
from app.realtime.dashboard_service import DashboardService
from app.realtime.observability import RealTimeObservability
from app.realtime.orchestrator import RealTimeOperationsOrchestrator


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Enum & Interface Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestEnumsAndInterfaces:
    def test_event_type_values(self):
        assert EventType.TRAIN_STARTED == "TRAIN_STARTED"
        assert EventType.TRAIN_CANCELLED == "TRAIN_CANCELLED"
        assert EventType.PLATFORM_CHANGED == "PLATFORM_CHANGED"
        assert EventType.INCIDENT_RESOLVED == "INCIDENT_RESOLVED"

    def test_train_status_values(self):
        assert TrainStatus.SCHEDULED == "SCHEDULED"
        assert TrainStatus.RUNNING == "RUNNING"
        assert TrainStatus.DELAYED == "DELAYED"
        assert TrainStatus.COMPLETED == "COMPLETED"

    def test_journey_status_values(self):
        assert JourneyStatus.PLANNED == "PLANNED"
        assert JourneyStatus.ONBOARD == "ONBOARD"
        assert JourneyStatus.DISRUPTED == "DISRUPTED"
        assert JourneyStatus.COMPLETED == "COMPLETED"

    def test_incident_severity_values(self):
        assert IncidentSeverity.LOW == "LOW"
        assert IncidentSeverity.CRITICAL == "CRITICAL"

    def test_notification_priority_values(self):
        assert NotificationPriority.URGENT == "URGENT"
        assert NotificationPriority.LOW == "LOW"

    def test_event_type_all_12_types(self):
        assert len(EventType) == 12


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Domain Model Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestDomainModels:
    def test_operational_event_creation(self):
        evt = OperationalEvent(
            event_id="evt-001",
            event_type=EventType.TRAIN_STARTED,
            train_number="12301",
            station_code="NDLS",
            timestamp="2026-07-28T10:00:00Z",
        )
        assert evt.event_id == "evt-001"
        assert evt.event_type == EventType.TRAIN_STARTED
        assert evt.train_number == "12301"
        assert evt.payload == {}

    def test_train_state_defaults(self):
        ts = TrainState(
            train_number="12301",
            current_station="NDLS",
            last_updated="2026-07-28T10:00:00Z",
        )
        assert ts.status == TrainStatus.SCHEDULED
        assert ts.delay_minutes == 0
        assert ts.speed_kmh == 0.0

    def test_journey_state_defaults(self):
        js = JourneyState(
            journey_id="j-001",
            passenger_id="p-001",
            train_number="12301",
            origin_station="NDLS",
            destination_station="HWH",
            eta_destination="2026-07-29T06:00:00Z",
            last_updated="2026-07-28T10:00:00Z",
        )
        assert js.status == JourneyStatus.PLANNED
        assert js.transfer_risk is False

    def test_incident_creation(self):
        inc = Incident(
            incident_id="inc-001",
            train_number="12301",
            severity=IncidentSeverity.CRITICAL,
            title="Service Cancelled",
            description="Full cancellation",
            affected_passengers_count=150,
            created_at="2026-07-28T10:00:00Z",
        )
        assert inc.resolved is False
        assert inc.affected_passengers_count == 150

    def test_eta_result_validation(self):
        eta = ETAResult(
            train_number="12301",
            station_code="HWH",
            scheduled_arrival="2026-07-29T06:00:00Z",
            predicted_eta="2026-07-29T07:30:00Z",
            delay_minutes=90,
            confidence_score=0.80,
            last_calculated="2026-07-28T10:00:00Z",
        )
        assert eta.delay_minutes == 90
        assert eta.confidence_score == 0.80

    def test_notification_payload(self):
        notif = NotificationPayload(
            notification_id="notif-001",
            journey_id="j-001",
            passenger_id="p-001",
            title="Travel Advisory",
            message="Your train is delayed.",
            priority=NotificationPriority.HIGH,
            dispatched_at="2026-07-28T10:00:00Z",
        )
        assert notif.priority == NotificationPriority.HIGH

    def test_dashboard_metrics_defaults(self):
        dm = DashboardMetrics(timestamp="2026-07-28T10:00:00Z")
        assert dm.total_events_processed == 0
        assert dm.system_health_status == "HEALTHY"

    def test_ai_context_model(self):
        ctx = RealTimeAIContext(train_number="12301")
        assert ctx.live_train_state is None
        assert ctx.active_incidents == []


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Event Factory Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestEventFactory:
    def test_create_event_basic(self):
        evt = EventFactory.create_event(
            event_type=EventType.TRAIN_STARTED,
            train_number="12301",
            station_code="NDLS",
        )
        assert evt.event_id.startswith("evt-")
        assert evt.event_type == EventType.TRAIN_STARTED
        assert evt.train_number == "12301"

    def test_create_event_with_payload(self):
        evt = EventFactory.create_event(
            event_type=EventType.TRAIN_DELAYED,
            train_number="12302",
            payload={"delay_minutes": 45},
        )
        assert evt.payload["delay_minutes"] == 45

    def test_create_event_unique_ids(self):
        e1 = EventFactory.create_event(EventType.TRAIN_STARTED, "12301")
        e2 = EventFactory.create_event(EventType.TRAIN_STARTED, "12301")
        assert e1.event_id != e2.event_id


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Event Gateway Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestEventGateway:
    def setup_method(self):
        self.gateway = RealTimeEventGateway()

    def test_valid_event_ingestion(self):
        raw = {
            "event_type": "TRAIN_STARTED",
            "train_number": "12301",
            "station_code": "NDLS",
        }
        event = self.gateway.validate_and_normalize(raw)
        assert event.event_type == EventType.TRAIN_STARTED
        assert event.train_number == "12301"

    def test_missing_train_number_raises(self):
        with pytest.raises(ValueError, match="train_number"):
            self.gateway.validate_and_normalize({"event_type": "TRAIN_STARTED"})

    def test_missing_event_type_raises(self):
        with pytest.raises(ValueError, match="event_type"):
            self.gateway.validate_and_normalize({"train_number": "12301"})

    def test_unsupported_event_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            self.gateway.validate_and_normalize(
                {"event_type": "UNKNOWN_TYPE", "train_number": "12301"}
            )

    def test_non_dict_raises(self):
        with pytest.raises(ValueError, match="dictionary"):
            self.gateway.validate_and_normalize("invalid")

    def test_case_insensitive_event_type(self):
        raw = {"event_type": "train_delayed", "train_number": "12301"}
        event = self.gateway.validate_and_normalize(raw)
        assert event.event_type == EventType.TRAIN_DELAYED

    def test_event_with_custom_id(self):
        raw = {
            "event_id": "custom-id-001",
            "event_type": "BOARDING_STARTED",
            "train_number": "12301",
        }
        event = self.gateway.validate_and_normalize(raw)
        assert event.event_id == "custom-id-001"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: Event Store Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestEventStore:
    def setup_method(self):
        self.store = EventStore()

    def _make_event(self, train="12301", etype=EventType.TRAIN_STARTED):
        return EventFactory.create_event(etype, train, "NDLS")

    def test_append_and_count(self):
        self.store.append(self._make_event())
        assert self.store.count() == 1

    def test_get_by_id(self):
        evt = self._make_event()
        self.store.append(evt)
        result = self.store.get_by_id(evt.event_id)
        assert result is not None
        assert result.event_id == evt.event_id

    def test_get_by_train(self):
        self.store.append(self._make_event("12301"))
        self.store.append(self._make_event("12302"))
        self.store.append(self._make_event("12301"))
        results = self.store.get_by_train("12301")
        assert len(results) == 2

    def test_get_all(self):
        self.store.append(self._make_event())
        self.store.append(self._make_event())
        assert len(self.store.get_all()) == 2

    def test_clear(self):
        self.store.append(self._make_event())
        self.store.clear()
        assert self.store.count() == 0

    def test_get_by_id_not_found(self):
        assert self.store.get_by_id("nonexistent") is None


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6: Event Dispatcher Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestEventDispatcher:
    def setup_method(self):
        self.dispatcher = EventDispatcher()
        self.received_events = []

    def _handler(self, event):
        self.received_events.append(event)

    @pytest.mark.anyio
    async def test_subscribe_and_dispatch(self):
        self.dispatcher.subscribe(EventType.TRAIN_STARTED, self._handler)
        evt = EventFactory.create_event(EventType.TRAIN_STARTED, "12301")
        await self.dispatcher.dispatch(evt)
        assert len(self.received_events) == 1

    @pytest.mark.anyio
    async def test_subscribe_all(self):
        self.dispatcher.subscribe_all(self._handler)
        evt = EventFactory.create_event(EventType.TRAIN_DELAYED, "12301")
        await self.dispatcher.dispatch(evt)
        assert len(self.received_events) == 1

    @pytest.mark.anyio
    async def test_no_matching_handler(self):
        self.dispatcher.subscribe(EventType.TRAIN_STARTED, self._handler)
        evt = EventFactory.create_event(EventType.TRAIN_DELAYED, "12301")
        await self.dispatcher.dispatch(evt)
        assert len(self.received_events) == 0


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7: Train Tracker / State Machine Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestTrainTracker:
    def setup_method(self):
        self.tracker = TrainTracker()

    def _event(self, etype, train="12301", station="NDLS", payload=None):
        return EventFactory.create_event(etype, train, station, payload)

    def test_initial_state_creation(self):
        evt = self._event(EventType.TRAIN_STARTED)
        state = self.tracker.update_state(evt)
        assert state.status == TrainStatus.DEPARTED
        assert state.train_number == "12301"

    def test_boarding_transition(self):
        evt = self._event(EventType.BOARDING_STARTED)
        state = self.tracker.update_state(evt)
        assert state.status == TrainStatus.BOARDING

    def test_departure_after_boarding(self):
        self.tracker.update_state(self._event(EventType.BOARDING_STARTED))
        state = self.tracker.update_state(self._event(EventType.BOARDING_COMPLETED))
        assert state.status == TrainStatus.DEPARTED

    def test_delay_transition(self):
        self.tracker.update_state(self._event(EventType.TRAIN_STARTED))
        state = self.tracker.update_state(
            self._event(EventType.TRAIN_DELAYED, payload={"delay_minutes": 60})
        )
        assert state.status == TrainStatus.DELAYED
        assert state.delay_minutes == 60

    def test_cancellation(self):
        state = self.tracker.update_state(self._event(EventType.TRAIN_CANCELLED))
        assert state.status == TrainStatus.CANCELLED

    def test_diversion(self):
        state = self.tracker.update_state(self._event(EventType.TRAIN_DIVERTED))
        assert state.status == TrainStatus.DIVERTED

    def test_platform_change(self):
        state = self.tracker.update_state(
            self._event(EventType.PLATFORM_CHANGED, payload={"new_platform": "5A"})
        )
        assert state.current_platform == "5A"

    def test_get_state(self):
        self.tracker.update_state(self._event(EventType.TRAIN_STARTED))
        result = self.tracker.get_state("12301")
        assert result is not None
        assert result.train_number == "12301"

    def test_get_state_not_found(self):
        assert self.tracker.get_state("99999") is None

    def test_get_all_states(self):
        self.tracker.update_state(self._event(EventType.TRAIN_STARTED, "12301"))
        self.tracker.update_state(self._event(EventType.TRAIN_STARTED, "12302"))
        assert len(self.tracker.get_all_states()) == 2

    def test_rescheduled_transition(self):
        state = self.tracker.update_state(self._event(EventType.TRAIN_RESCHEDULED))
        assert state.status == TrainStatus.DELAYED

    def test_speed_update(self):
        state = self.tracker.update_state(
            self._event(EventType.TRAIN_STARTED, payload={"speed_kmh": 120.5})
        )
        assert state.speed_kmh == 120.5


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8: Journey Tracker Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestJourneyTracker:
    def setup_method(self):
        self.tracker = JourneyTracker()
        self.journey = self.tracker.register_journey(
            journey_id="j-001",
            passenger_id="p-001",
            train_number="12301",
            origin_station="NDLS",
            destination_station="HWH",
            scheduled_eta="2026-07-29T06:00:00Z",
        )

    def test_register_journey(self):
        assert self.journey.journey_id == "j-001"
        assert self.journey.status == JourneyStatus.PLANNED

    def test_get_journey(self):
        result = self.tracker.get_journey("j-001")
        assert result is not None
        assert result.passenger_id == "p-001"

    def test_get_journey_not_found(self):
        assert self.tracker.get_journey("nonexistent") is None

    def test_get_journeys_by_train(self):
        self.tracker.register_journey("j-002", "p-002", "12301", "NDLS", "HWH", "X")
        results = self.tracker.get_journeys_by_train("12301")
        assert len(results) == 2

    def test_boarding_transition(self):
        evt = EventFactory.create_event(EventType.BOARDING_STARTED, "12301", "NDLS")
        updated = self.tracker.update_journey_with_event("j-001", evt)
        assert updated is not None
        assert updated.status == JourneyStatus.BOARDING

    def test_onboard_transition(self):
        evt = EventFactory.create_event(EventType.TRAIN_STARTED, "12301", "NDLS")
        updated = self.tracker.update_journey_with_event("j-001", evt)
        assert updated.status == JourneyStatus.ONBOARD

    def test_disruption_on_severe_delay(self):
        train_state = TrainState(
            train_number="12301",
            current_station="CNB",
            status=TrainStatus.DELAYED,
            delay_minutes=60,
            last_updated="2026-07-28T12:00:00Z",
        )
        evt = EventFactory.create_event(EventType.TRAIN_DELAYED, "12301")
        updated = self.tracker.update_journey_with_event("j-001", evt, train_state)
        assert updated.status == JourneyStatus.DISRUPTED

    def test_cancellation_transition(self):
        evt = EventFactory.create_event(EventType.TRAIN_CANCELLED, "12301")
        updated = self.tracker.update_journey_with_event("j-001", evt)
        assert updated.status == JourneyStatus.CANCELLED

    def test_transfer_risk_flag(self):
        train_state = TrainState(
            train_number="12301",
            current_station="CNB",
            status=TrainStatus.DELAYED,
            delay_minutes=35,
            last_updated="2026-07-28T12:00:00Z",
        )
        evt = EventFactory.create_event(EventType.TRAIN_STARTED, "12301")
        updated = self.tracker.update_journey_with_event("j-001", evt, train_state)
        assert updated.transfer_risk is True

    def test_update_nonexistent_journey(self):
        evt = EventFactory.create_event(EventType.TRAIN_STARTED, "12301")
        result = self.tracker.update_journey_with_event("nonexistent", evt)
        assert result is None


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9: ETA Engine Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestETAEngine:
    def setup_method(self):
        self.engine = ETAEngine()

    def test_on_time_eta(self):
        ts = TrainState(
            train_number="12301",
            current_station="CNB",
            status=TrainStatus.RUNNING,
            delay_minutes=0,
            last_updated="2026-07-28T12:00:00Z",
        )
        result = self.engine.calculate_eta(ts, "HWH", "2026-07-29T06:00:00Z")
        assert result.delay_minutes == 0
        assert result.confidence_score == 0.95

    def test_delayed_eta(self):
        ts = TrainState(
            train_number="12301",
            current_station="CNB",
            status=TrainStatus.DELAYED,
            delay_minutes=90,
            last_updated="2026-07-28T12:00:00Z",
        )
        result = self.engine.calculate_eta(ts, "HWH", "2026-07-29T06:00:00Z")
        assert result.delay_minutes == 90
        assert result.confidence_score == 0.80

    def test_eta_station_code(self):
        ts = TrainState(
            train_number="12301",
            current_station="CNB",
            status=TrainStatus.RUNNING,
            delay_minutes=0,
            last_updated="2026-07-28T12:00:00Z",
        )
        result = self.engine.calculate_eta(ts, "PRYJ", "2026-07-29T04:00:00Z")
        assert result.station_code == "PRYJ"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 10: Incident Engine Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestIncidentEngine:
    def setup_method(self):
        self.engine = IncidentEngine()

    def test_cancellation_creates_critical_incident(self):
        evt = EventFactory.create_event(EventType.TRAIN_CANCELLED, "12301")
        incidents = self.engine.evaluate_event_for_incidents(evt)
        assert len(incidents) == 1
        assert incidents[0].severity == IncidentSeverity.CRITICAL

    def test_platform_change_creates_high_incident(self):
        evt = EventFactory.create_event(
            EventType.PLATFORM_CHANGED, "12301", "NDLS", {"new_platform": "5A"}
        )
        incidents = self.engine.evaluate_event_for_incidents(evt)
        assert len(incidents) == 1
        assert incidents[0].severity == IncidentSeverity.HIGH

    def test_delay_below_threshold_no_incident(self):
        ts = TrainState(
            train_number="12301",
            current_station="CNB",
            status=TrainStatus.DELAYED,
            delay_minutes=30,
            last_updated="2026-07-28T12:00:00Z",
        )
        evt = EventFactory.create_event(
            EventType.TRAIN_DELAYED, "12301", payload={"delay_minutes": 30}
        )
        incidents = self.engine.evaluate_event_for_incidents(evt, ts)
        assert len(incidents) == 0

    def test_delay_above_threshold_creates_incident(self):
        ts = TrainState(
            train_number="12301",
            current_station="CNB",
            status=TrainStatus.DELAYED,
            delay_minutes=90,
            last_updated="2026-07-28T12:00:00Z",
        )
        evt = EventFactory.create_event(
            EventType.TRAIN_DELAYED, "12301", payload={"delay_minutes": 90}
        )
        incidents = self.engine.evaluate_event_for_incidents(evt, ts)
        assert len(incidents) == 1

    def test_get_active_incidents(self):
        evt = EventFactory.create_event(EventType.TRAIN_CANCELLED, "12301")
        self.engine.evaluate_event_for_incidents(evt)
        active = self.engine.get_active_incidents()
        assert len(active) == 1

    def test_resolve_incident(self):
        evt = EventFactory.create_event(EventType.TRAIN_CANCELLED, "12301")
        incidents = self.engine.evaluate_event_for_incidents(evt)
        self.engine.resolve_incident(incidents[0].incident_id)
        active = self.engine.get_active_incidents()
        assert len(active) == 0

    def test_resolve_nonexistent_returns_false(self):
        assert self.engine.resolve_incident("nonexistent") is False

    def test_affected_passenger_count(self):
        js = JourneyState(
            journey_id="j-001",
            passenger_id="p-001",
            train_number="12301",
            origin_station="NDLS",
            destination_station="HWH",
            eta_destination="X",
            last_updated="X",
        )
        evt = EventFactory.create_event(EventType.TRAIN_CANCELLED, "12301")
        incidents = self.engine.evaluate_event_for_incidents(evt, affected_journeys=[js])
        assert incidents[0].affected_passengers_count == 1


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 11: Decision Engine Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestDecisionEngine:
    def setup_method(self):
        self.engine = DecisionEngine()
        self.journey = JourneyState(
            journey_id="j-001",
            passenger_id="p-001",
            train_number="12301",
            origin_station="NDLS",
            destination_station="HWH",
            eta_destination="2026-07-29T06:00:00Z",
            last_updated="2026-07-28T12:00:00Z",
            transfer_risk=True,
        )

    def _incident(self, severity):
        return Incident(
            incident_id="inc-001",
            train_number="12301",
            severity=severity,
            title="Test Incident",
            description="Test",
            created_at="2026-07-28T12:00:00Z",
        )

    def test_critical_recommendations(self):
        recs = self.engine.generate_recommendations(
            self._incident(IncidentSeverity.CRITICAL), self.journey
        )
        assert len(recs) >= 2
        assert any("re-booking" in r for r in recs)

    def test_high_severity_with_transfer_risk(self):
        recs = self.engine.generate_recommendations(
            self._incident(IncidentSeverity.HIGH), self.journey
        )
        assert any("connection" in r.lower() or "transfer" in r.lower() or "connecting" in r.lower() for r in recs)

    def test_medium_recommendations(self):
        recs = self.engine.generate_recommendations(
            self._incident(IncidentSeverity.MEDIUM), self.journey
        )
        assert len(recs) >= 1

    def test_low_recommendations(self):
        recs = self.engine.generate_recommendations(
            self._incident(IncidentSeverity.LOW), self.journey
        )
        assert any("No immediate action" in r for r in recs)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 12: Notification Engine Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestNotificationEngine:
    def setup_method(self):
        self.engine = NotificationEngine()
        self.journey = JourneyState(
            journey_id="j-001",
            passenger_id="p-001",
            train_number="12301",
            origin_station="NDLS",
            destination_station="HWH",
            eta_destination="X",
            last_updated="X",
        )
        self.incident = Incident(
            incident_id="inc-001",
            train_number="12301",
            severity=IncidentSeverity.CRITICAL,
            title="Cancellation",
            description="Service cancelled",
            created_at="X",
        )

    def test_dispatch_notification(self):
        n = self.engine.orchestrate_notification(self.journey, self.incident)
        assert n.notification_id.startswith("notif-")
        assert n.priority == NotificationPriority.URGENT

    def test_custom_message(self):
        n = self.engine.orchestrate_notification(
            self.journey, self.incident, "Custom alert message"
        )
        assert n.message == "Custom alert message"

    def test_history_tracking(self):
        self.engine.orchestrate_notification(self.journey, self.incident)
        self.engine.orchestrate_notification(self.journey, self.incident)
        assert len(self.engine.get_history()) == 2

    def test_get_by_journey(self):
        self.engine.orchestrate_notification(self.journey, self.incident)
        results = self.engine.get_notifications_by_journey("j-001")
        assert len(results) == 1

    def test_priority_mapping_high(self):
        inc = Incident(
            incident_id="inc-002",
            train_number="12301",
            severity=IncidentSeverity.HIGH,
            title="Delay",
            description="Delay",
            created_at="X",
        )
        n = self.engine.orchestrate_notification(self.journey, inc)
        assert n.priority == NotificationPriority.HIGH


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 13: Dashboard Service Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestDashboardService:
    def setup_method(self):
        self.store = EventStore()
        self.train_tracker = TrainTracker()
        self.journey_tracker = JourneyTracker()
        self.incident_engine = IncidentEngine()
        self.dashboard = DashboardService(
            self.store, self.train_tracker, self.journey_tracker, self.incident_engine
        )

    def test_empty_metrics(self):
        m = self.dashboard.get_metrics()
        assert m.total_events_processed == 0
        assert m.system_health_status == "HEALTHY"
        assert m.on_time_performance_percent == 100.0

    def test_metrics_with_data(self):
        evt = EventFactory.create_event(EventType.TRAIN_STARTED, "12301", "NDLS")
        self.store.append(evt)
        self.train_tracker.update_state(evt)
        m = self.dashboard.get_metrics()
        assert m.total_events_processed == 1
        assert m.active_trains_count == 1

    def test_degraded_health_on_delay(self):
        delay_evt = EventFactory.create_event(
            EventType.TRAIN_DELAYED, "12301", "NDLS", {"delay_minutes": 30}
        )
        self.store.append(delay_evt)
        self.train_tracker.update_state(delay_evt)
        m = self.dashboard.get_metrics()
        assert m.system_health_status == "DEGRADED"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 14: Observability Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestObservability:
    def setup_method(self):
        self.obs = RealTimeObservability()

    def test_initial_counters(self):
        snap = self.obs.get_metrics_snapshot()
        assert snap["counters"]["events_ingested"] == 0
        assert snap["status"] == "HEALTHY"

    def test_record_events(self):
        self.obs.record_event_ingested()
        self.obs.record_event_ingested()
        snap = self.obs.get_metrics_snapshot()
        assert snap["counters"]["events_ingested"] == 2

    def test_record_incident(self):
        self.obs.record_incident_detected()
        snap = self.obs.get_metrics_snapshot()
        assert snap["counters"]["incidents_detected"] == 1

    def test_record_notification(self):
        self.obs.record_notification_dispatched()
        snap = self.obs.get_metrics_snapshot()
        assert snap["counters"]["notifications_dispatched"] == 1

    def test_latency_tracker(self):
        with self.obs.record_latency():
            x = sum(range(1000))  # noqa: F841
        snap = self.obs.get_metrics_snapshot()
        assert snap["last_processing_latency_ms"] > 0

    def test_error_status(self):
        self.obs.record_error()
        snap = self.obs.get_metrics_snapshot()
        assert snap["status"] == "DEGRADED"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 15: Orchestrator Integration Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestOrchestrator:
    def setup_method(self):
        self.orch = RealTimeOperationsOrchestrator()

    @pytest.mark.anyio
    async def test_process_raw_event(self):
        raw = {"event_type": "TRAIN_STARTED", "train_number": "12301", "station_code": "NDLS"}
        event = await self.orch.process_raw_event(raw)
        assert event.event_type == EventType.TRAIN_STARTED
        assert self.orch.store.count() == 1

    @pytest.mark.anyio
    async def test_train_state_updated_after_event(self):
        await self.orch.process_raw_event(
            {"event_type": "TRAIN_STARTED", "train_number": "12301", "station_code": "NDLS"}
        )
        state = self.orch.get_train_state("12301")
        assert state is not None
        assert state.status == TrainStatus.DEPARTED

    @pytest.mark.anyio
    async def test_journey_registration_and_monitoring(self):
        self.orch.register_passenger_journey(
            "j-001", "p-001", "12301", "NDLS", "HWH", "2026-07-29T06:00:00Z"
        )
        await self.orch.process_raw_event(
            {"event_type": "BOARDING_STARTED", "train_number": "12301", "station_code": "NDLS"}
        )
        j = self.orch.get_journey_state("j-001")
        assert j is not None
        assert j.status == JourneyStatus.BOARDING

    @pytest.mark.anyio
    async def test_incident_detection_on_cancellation(self):
        self.orch.register_passenger_journey(
            "j-001", "p-001", "12301", "NDLS", "HWH", "2026-07-29T06:00:00Z"
        )
        await self.orch.process_raw_event(
            {"event_type": "TRAIN_CANCELLED", "train_number": "12301"}
        )
        incidents = self.orch.incident_engine.get_active_incidents()
        assert len(incidents) >= 1
        assert incidents[0].severity == IncidentSeverity.CRITICAL

    @pytest.mark.anyio
    async def test_notification_dispatched_on_incident(self):
        self.orch.register_passenger_journey(
            "j-001", "p-001", "12301", "NDLS", "HWH", "2026-07-29T06:00:00Z"
        )
        await self.orch.process_raw_event(
            {"event_type": "TRAIN_CANCELLED", "train_number": "12301"}
        )
        history = self.orch.notification_engine.get_history()
        assert len(history) >= 1

    @pytest.mark.anyio
    async def test_dashboard_metrics_after_processing(self):
        await self.orch.process_raw_event(
            {"event_type": "TRAIN_STARTED", "train_number": "12301", "station_code": "NDLS"}
        )
        metrics = self.orch.get_dashboard_metrics()
        assert metrics.total_events_processed == 1
        assert metrics.active_trains_count == 1

    @pytest.mark.anyio
    async def test_observability_counters_increment(self):
        await self.orch.process_raw_event(
            {"event_type": "TRAIN_STARTED", "train_number": "12301"}
        )
        snap = self.orch.observability.get_metrics_snapshot()
        assert snap["counters"]["events_ingested"] == 1

    def test_dynamic_eta_calculation(self):
        result = self.orch.calculate_dynamic_eta("12301", "HWH", "2026-07-29T06:00:00Z")
        assert result.station_code == "HWH"

    @pytest.mark.anyio
    async def test_ai_context_generation(self):
        self.orch.register_passenger_journey(
            "j-001", "p-001", "12301", "NDLS", "HWH", "2026-07-29T06:00:00Z"
        )
        await self.orch.process_raw_event(
            {"event_type": "TRAIN_STARTED", "train_number": "12301", "station_code": "NDLS"}
        )
        ctx = self.orch.get_live_ai_context("12301", "j-001")
        assert ctx.train_number == "12301"
        assert ctx.live_train_state is not None
        assert ctx.active_journey_state is not None

    @pytest.mark.anyio
    async def test_invalid_event_raises(self):
        with pytest.raises(ValueError):
            await self.orch.process_raw_event({"train_number": "12301"})

    @pytest.mark.anyio
    async def test_multiple_events_sequential(self):
        await self.orch.process_raw_event(
            {"event_type": "BOARDING_STARTED", "train_number": "12301", "station_code": "NDLS"}
        )
        await self.orch.process_raw_event(
            {"event_type": "BOARDING_COMPLETED", "train_number": "12301", "station_code": "NDLS"}
        )
        await self.orch.process_raw_event(
            {"event_type": "TRAIN_STARTED", "train_number": "12301", "station_code": "NDLS"}
        )
        state = self.orch.get_train_state("12301")
        assert state.status == TrainStatus.DEPARTED
        assert self.orch.store.count() == 3


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 16: REST API Endpoint Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestRealtimeAPI:
    def setup_method(self):
        from app.main import app
        self.client = TestClient(app)

    def test_health_endpoint(self):
        resp = self.client.get("/api/realtime/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "UP"
        assert body["platform"] == "Real-Time Operations"

    def test_ingest_event(self):
        resp = self.client.post(
            "/api/realtime/events",
            json={"event_type": "TRAIN_STARTED", "train_number": "12301", "station_code": "NDLS"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "INGESTED"

    def test_ingest_invalid_event(self):
        resp = self.client.post(
            "/api/realtime/events",
            json={"train_number": "12301"},
        )
        assert resp.status_code == 400

    def test_get_train_state(self):
        self.client.post(
            "/api/realtime/events",
            json={"event_type": "TRAIN_STARTED", "train_number": "12301", "station_code": "NDLS"},
        )
        resp = self.client.get("/api/realtime/trains/12301")
        assert resp.status_code == 200
        assert resp.json()["train_number"] == "12301"

    def test_get_train_state_not_found(self):
        resp = self.client.get("/api/realtime/trains/99999")
        assert resp.status_code == 404

    def test_register_and_get_journey(self):
        self.client.post(
            "/api/realtime/journeys/register",
            json={
                "journey_id": "j-api-001",
                "passenger_id": "p-api-001",
                "train_number": "12301",
                "origin_station": "NDLS",
                "destination_station": "HWH",
                "scheduled_eta": "2026-07-29T06:00:00Z",
            },
        )
        resp = self.client.get("/api/realtime/journeys/j-api-001")
        assert resp.status_code == 200
        assert resp.json()["journey_id"] == "j-api-001"

    def test_get_journey_not_found(self):
        resp = self.client.get("/api/realtime/journeys/nonexistent")
        assert resp.status_code == 404

    def test_get_eta(self):
        resp = self.client.get(
            "/api/realtime/eta/12301/HWH?scheduled_arrival=2026-07-29T06:00:00Z"
        )
        assert resp.status_code == 200
        assert resp.json()["station_code"] == "HWH"

    def test_get_incidents(self):
        resp = self.client.get("/api/realtime/incidents")
        assert resp.status_code == 200
        assert "incidents" in resp.json()

    def test_get_dashboard(self):
        resp = self.client.get("/api/realtime/dashboard")
        assert resp.status_code == 200
        assert "total_events_processed" in resp.json()

    def test_ai_context_endpoint(self):
        self.client.post(
            "/api/realtime/events",
            json={"event_type": "TRAIN_STARTED", "train_number": "12301", "station_code": "NDLS"},
        )
        resp = self.client.get("/api/realtime/ai-context/12301")
        assert resp.status_code == 200
        assert resp.json()["train_number"] == "12301"
