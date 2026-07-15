# app/booking/candidate/builder.py
import uuid
from typing import List, Dict, Any
from app.booking.interfaces.contracts import IBookingCandidateBuilder
from app.booking.dto.models import BookingCandidateDTO


class BookingCandidateBuilder(IBookingCandidateBuilder):
    def build_booking_candidates(
        self, journey_dto: Any, profile: Dict[str, Any]
    ) -> List[BookingCandidateDTO]:
        candidates = []

        # Simulates candidate construction by joining journey with commercial choices
        # Option 1: General Quota GN on 3AC
        candidates.append(
            BookingCandidateDTO(
                candidate_id=f"cand_gn_{uuid.uuid4().hex[:8]}",
                journey_id=journey_dto.get("journey_id", "jrn_01")
                if journey_dto
                else "jrn_01",
                segments=[{"train_number": "12002", "from": "NDLS", "to": "BPL"}],
                selected_quota="GN",
                boarding_point="NDLS",
                class_code="3A",
                estimated_fare=1200.0,
            )
        )

        # Option 2: Senior Citizen Quota SS on 2AC (if eligible)
        candidates.append(
            BookingCandidateDTO(
                candidate_id=f"cand_ss_{uuid.uuid4().hex[:8]}",
                journey_id=journey_dto.get("journey_id", "jrn_01")
                if journey_dto
                else "jrn_01",
                segments=[{"train_number": "12002", "from": "NDLS", "to": "BPL"}],
                selected_quota="SS",
                boarding_point="NDLS",
                class_code="2A",
                estimated_fare=1800.0,
            )
        )

        return candidates
