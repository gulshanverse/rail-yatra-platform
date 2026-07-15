# app/booking/boarding/optimizer.py
from typing import Dict, Any
from app.booking.interfaces.contracts import IBoardingEngine
from app.booking.dto.models import BookingCandidateDTO, BoardingDTO


class BoardingEngine(IBoardingEngine):
    def optimize_boarding(
        self, candidate: BookingCandidateDTO, profile: Dict[str, Any]
    ) -> BoardingDTO:
        # Resolves alternative station boarding point changes
        boarding_point = candidate.boarding_point
        original = candidate.boarding_point
        changed = False
        offset_km = 0.0
        risk = "LOW"

        # If requested boarding offset is enabled in traveler profile preferences
        if (
            profile.get("enable_boarding_shift", False)
            and candidate.selected_quota == "GN"
        ):
            # Simulate shift boarding point to train origin to bypass ticket limits
            boarding_point = "NDLS"  # Origin station
            changed = True
            offset_km = 45.0
            risk = "MEDIUM"  # no-show risk checks required

        return BoardingDTO(
            boarding_station=boarding_point,
            original_boarding_station=original,
            boarding_point_changed=changed,
            distance_offset_km=offset_km,
            no_show_risk=risk,
        )
