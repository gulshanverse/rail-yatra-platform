"""
Live Train State Tracker: Maintains authoritative train operational status and location.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List
from app.realtime.interfaces import EventType, TrainStatus
from app.realtime.models import OperationalEvent, TrainState

logger = logging.getLogger("ai-service.realtime.train_tracker")


class TrainTracker:
    def __init__(self) -> None:
        self._train_states: Dict[str, TrainState] = {}

    def get_state(self, train_number: str) -> Optional[TrainState]:
        """Returns the current state for a given train number."""
        return self._train_states.get(train_number)

    def get_all_states(self) -> List[TrainState]:
        """Returns state snapshots of all tracked trains."""
        return list(self._train_states.values())

    def update_state(self, event: OperationalEvent) -> TrainState:
        """Processes an operational event to update the state machine of the train."""
        now_str = datetime.now(timezone.utc).isoformat()
        current = self._train_states.get(event.train_number)

        if not current:
            current = TrainState(
                train_number=event.train_number,
                current_station=event.station_code or "ORIGIN",
                status=TrainStatus.SCHEDULED,
                delay_minutes=0,
                last_updated=now_str,
            )

        payload = event.payload or {}
        new_station = event.station_code or payload.get("station_code") or current.current_station
        new_next_station = payload.get("next_station", current.next_station)
        delay = payload.get("delay_minutes", current.delay_minutes)
        platform = payload.get("platform", current.current_platform)
        speed = payload.get("speed_kmh", current.speed_kmh)

        status = current.status
        if event.event_type == EventType.TRAIN_STARTED:
            status = TrainStatus.DEPARTED
        elif event.event_type == EventType.BOARDING_STARTED:
            status = TrainStatus.BOARDING
        elif event.event_type == EventType.BOARDING_COMPLETED:
            status = TrainStatus.DEPARTED
        elif event.event_type == EventType.TRAIN_STOPPED:
            status = TrainStatus.DELAYED
        elif event.event_type == EventType.TRAIN_DELAYED:
            status = TrainStatus.DELAYED
        elif event.event_type == EventType.TRAIN_DIVERTED:
            status = TrainStatus.DIVERTED
        elif event.event_type == EventType.TRAIN_CANCELLED:
            status = TrainStatus.CANCELLED
        elif event.event_type == EventType.PLATFORM_CHANGED:
            platform = payload.get("new_platform", platform)
        elif event.event_type == EventType.TRAIN_RESCHEDULED:
            status = TrainStatus.DELAYED

        # Enforce state machine transition validation
        allowed = {
            TrainStatus.SCHEDULED: {TrainStatus.SCHEDULED, TrainStatus.BOARDING, TrainStatus.DEPARTED, TrainStatus.RUNNING, TrainStatus.DELAYED, TrainStatus.CANCELLED, TrainStatus.DIVERTED},
            TrainStatus.BOARDING: {TrainStatus.BOARDING, TrainStatus.DEPARTED, TrainStatus.RUNNING, TrainStatus.CANCELLED},
            TrainStatus.DEPARTED: {TrainStatus.DEPARTED, TrainStatus.RUNNING, TrainStatus.DELAYED, TrainStatus.DIVERTED, TrainStatus.ARRIVED, TrainStatus.CANCELLED},
            TrainStatus.RUNNING: {TrainStatus.RUNNING, TrainStatus.DELAYED, TrainStatus.DIVERTED, TrainStatus.ARRIVED, TrainStatus.CANCELLED},
            TrainStatus.DELAYED: {TrainStatus.RUNNING, TrainStatus.DELAYED, TrainStatus.DIVERTED, TrainStatus.ARRIVED, TrainStatus.CANCELLED},
            TrainStatus.DIVERTED: {TrainStatus.RUNNING, TrainStatus.DELAYED, TrainStatus.DIVERTED, TrainStatus.ARRIVED, TrainStatus.CANCELLED},
            TrainStatus.ARRIVED: {TrainStatus.ARRIVED, TrainStatus.COMPLETED},
            TrainStatus.CANCELLED: {TrainStatus.CANCELLED},
            TrainStatus.COMPLETED: {TrainStatus.COMPLETED},
        }

        train_existed = event.train_number in self._train_states
        if train_existed and status != current.status:
            if status not in allowed.get(current.status, set()):
                logger.warning(
                    f"Rejected invalid train status transition from {current.status} to {status} for train {event.train_number}."
                )
                status = current.status

        updated = TrainState(
            train_number=event.train_number,
            current_station=new_station,
            next_station=new_next_station,
            status=status,
            delay_minutes=int(delay) if delay is not None else 0,
            current_platform=str(platform) if platform is not None else None,
            speed_kmh=float(speed) if speed is not None else 0.0,
            last_updated=now_str,
        )

        self._train_states[event.train_number] = updated
        return updated

