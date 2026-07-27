"""
Passenger Journey Tracker: Manages live passenger travel state and connection monitoring.
"""

from datetime import datetime, timezone
from typing import Dict, Optional, List
from app.realtime.interfaces import EventType, JourneyStatus
from app.realtime.models import OperationalEvent, JourneyState, TrainState


class JourneyTracker:
    def __init__(self) -> None:
        self._journeys: Dict[str, JourneyState] = {}

    def register_journey(
        self,
        journey_id: str,
        passenger_id: str,
        train_number: str,
        origin_station: str,
        destination_station: str,
        scheduled_eta: str,
    ) -> JourneyState:
        """Registers a new active passenger journey for real-time tracking."""
        now_str = datetime.now(timezone.utc).isoformat()
        state = JourneyState(
            journey_id=journey_id,
            passenger_id=passenger_id,
            train_number=train_number,
            status=JourneyStatus.PLANNED,
            origin_station=origin_station,
            destination_station=destination_station,
            current_station=origin_station,
            eta_destination=scheduled_eta,
            transfer_risk=False,
            last_updated=now_str,
        )
        self._journeys[journey_id] = state
        return state

    def get_journey(self, journey_id: str) -> Optional[JourneyState]:
        """Returns the journey state by ID."""
        return self._journeys.get(journey_id)

    def get_journeys_by_train(self, train_number: str) -> List[JourneyState]:
        """Returns all passenger journeys associated with a specific train."""
        return [j for j in self._journeys.values() if j.train_number == train_number]

    def get_all_journeys(self) -> List[JourneyState]:
        """Returns all active journeys."""
        return list(self._journeys.values())

    def update_journey_with_event(
        self, journey_id: str, event: OperationalEvent, train_state: Optional[TrainState] = None
    ) -> Optional[JourneyState]:
        """Updates journey state based on operational events and train state."""
        journey = self._journeys.get(journey_id)
        if not journey:
            return None

        now_str = datetime.now(timezone.utc).isoformat()
        new_status = journey.status
        transfer_risk = journey.transfer_risk
        current_station = journey.current_station

        if train_state:
            current_station = train_state.current_station
            if train_state.delay_minutes > 30:
                transfer_risk = True

        if event.event_type == EventType.BOARDING_STARTED:
            new_status = JourneyStatus.BOARDING
        elif event.event_type in (EventType.TRAIN_STARTED, EventType.BOARDING_COMPLETED):
            new_status = JourneyStatus.ONBOARD
        elif event.event_type in (EventType.TRAIN_DELAYED, EventType.TRAIN_STOPPED):
            if train_state and train_state.delay_minutes > 45:
                new_status = JourneyStatus.DISRUPTED
        elif event.event_type == EventType.TRAIN_CANCELLED:
            new_status = JourneyStatus.CANCELLED

        updated = JourneyState(
            journey_id=journey.journey_id,
            passenger_id=journey.passenger_id,
            train_number=journey.train_number,
            status=new_status,
            origin_station=journey.origin_station,
            destination_station=journey.destination_station,
            current_station=current_station,
            eta_destination=journey.eta_destination,
            transfer_risk=transfer_risk,
            last_updated=now_str,
        )

        self._journeys[journey_id] = updated
        return updated
