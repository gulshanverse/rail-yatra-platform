"""
Dynamic ETA Recalculation Engine for Phase 8 Real-Time Operations Platform.
"""

from datetime import datetime, timezone, timedelta
from app.realtime.models import TrainState, ETAResult


class ETAEngine:
    def calculate_eta(
        self, train_state: TrainState, target_station: str, scheduled_arrival_iso: str
    ) -> ETAResult:
        """Calculates dynamic ETA for a given train state and target station."""
        now_str = datetime.now(timezone.utc).isoformat()
        try:
            scheduled_dt = datetime.fromisoformat(scheduled_arrival_iso.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            scheduled_dt = datetime.now(timezone.utc) + timedelta(hours=2)

        delay_mins = train_state.delay_minutes if train_state else 0
        predicted_dt = scheduled_dt + timedelta(minutes=delay_mins)

        confidence = 0.95
        if delay_mins > 60:
            confidence = 0.80
        elif delay_mins > 120:
            confidence = 0.65

        return ETAResult(
            train_number=train_state.train_number if train_state else "UNKNOWN",
            station_code=target_station,
            scheduled_arrival=scheduled_arrival_iso,
            predicted_eta=predicted_dt.isoformat(),
            delay_minutes=delay_mins,
            confidence_score=confidence,
            last_calculated=now_str,
        )
