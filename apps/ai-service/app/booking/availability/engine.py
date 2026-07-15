# app/booking/availability/engine.py
import time
from typing import List, Dict
from app.booking.interfaces.contracts import IAvailabilityEngine
from app.booking.dto.models import BookingCandidateDTO, AvailabilityDTO


class AvailabilityEngine(IAvailabilityEngine):
    async def verify_availability(
        self, candidates: List[BookingCandidateDTO]
    ) -> Dict[str, AvailabilityDTO]:
        availability_map = {}
        now = time.time()

        for candidate in candidates:
            # Simulated backend lookup: GN has active confirmed seats, SS is waitlisted
            if candidate.selected_quota == "GN":
                availability_map[candidate.candidate_id] = AvailabilityDTO(
                    status="AVAILABLE",
                    available_seats=15,
                    waitlist_position=0,
                    freshness_timestamp=now,
                )
            else:
                availability_map[candidate.candidate_id] = AvailabilityDTO(
                    status="WL",
                    available_seats=0,
                    waitlist_position=5,
                    freshness_timestamp=now,
                )

        return availability_map
