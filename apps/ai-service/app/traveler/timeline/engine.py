# app/traveler/timeline/engine.py
from typing import Any
from app.traveler.interfaces.contracts import ITimelineEngine
from app.traveler.dto.models import TravelerTimelineDTO, TravelerCheckpointDTO


class TimelineEngine(ITimelineEngine):
    def evaluate_timeline(self, context: Any) -> TravelerTimelineDTO:
        # Enforces drift metrics updates
        drift = context.telemetry.get("drift_minutes", 0.0)

        checkpoints = [
            TravelerCheckpointDTO(
                checkpoint_id="chk_01",
                station_code="NDLS",
                scheduled_arrival=1781577000.0,
                actual_arrival=1781577000.0,
                variance_minutes=0.0,
            ),
            TravelerCheckpointDTO(
                checkpoint_id="chk_02",
                station_code="BPL",
                scheduled_arrival=1781599000.0,
                actual_arrival=1781599000.0 + (drift * 60.0),
                variance_minutes=drift,
            ),
        ]

        # Increment timeline version if drift is detected
        version = "T_V2" if drift > 0 else "T_V1"

        return TravelerTimelineDTO(
            timeline_id="tim_01", version=version, events=checkpoints
        )
