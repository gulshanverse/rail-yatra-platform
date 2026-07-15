# app/journey/candidate/builder.py
import uuid
from typing import List, Any
from datetime import datetime, timedelta
from app.journey.interfaces.contracts import IJourneyCandidateBuilder
from app.journey.dto.models import JourneyCandidateDTO, SegmentDTO, TransferDTO
from app.journey.config.registry import get_policy


class JourneyCandidateBuilder(IJourneyCandidateBuilder):
    def __init__(self, intelligence_gateway: Any = None):
        self.intelligence_gateway = intelligence_gateway

    async def build_candidates(
        self, origin: str, destination: str, earliest_dep: datetime, latest_arr: datetime
    ) -> List[JourneyCandidateDTO]:
        # Clean inputs
        origin = origin.upper().strip()
        destination = destination.upper().strip()

        # Hard constraint check: origin != destination
        if origin == destination:
            return []

        candidates = []

        # Mocking routing logic: 
        # In a real environment, we'd search station schedules via Phase 5.2.
        # Here, we generate a direct candidate and a connecting candidate for evaluation.

        # Candidate 1: Direct Train Express (e.g. Train 12002 Bhopal Express)
        # Departing NDLS to BPL
        dep_time_1 = earliest_dep + timedelta(hours=2)
        arr_time_1 = dep_time_1 + timedelta(hours=8)
        if arr_time_1 <= latest_arr:
            direct_candidate = JourneyCandidateDTO(
                journey_id=f"jrn_dir_{uuid.uuid4().hex[:8]}",
                segments=[
                    SegmentDTO(
                        segment_id=f"seg_{uuid.uuid4().hex[:8]}",
                        train_number="12002",
                        boarding_station=origin,
                        alighting_station=destination,
                        scheduled_departure=dep_time_1,
                        scheduled_arrival=arr_time_1,
                        scheduled_boarding_platform="1",
                        scheduled_alighting_platform="3"
                    )
                ],
                transfers=[],
                total_distance_km=700,
                scheduled_duration_minutes=480
            )
            candidates.append(direct_candidate)

        # Candidate 2: Multi-leg Connecting Itinerary (NDLS -> JHS -> BPL)
        # Leg A: NDLS -> JHS (Train 12002)
        # Leg B: JHS -> BPL (Train 12626)
        dep_time_a = earliest_dep + timedelta(hours=1)
        arr_time_a = dep_time_a + timedelta(hours=5) # 5 hour leg

        transfer_station = "JHS"
        # 45 min buffer time
        dep_time_b = arr_time_a + timedelta(minutes=45)
        arr_time_b = dep_time_b + timedelta(hours=3) # 3 hour leg

        if arr_time_b <= latest_arr:
            connecting_candidate = JourneyCandidateDTO(
                journey_id=f"jrn_con_{uuid.uuid4().hex[:8]}",
                segments=[
                    SegmentDTO(
                        segment_id="seg_leg_a",
                        train_number="12002",
                        boarding_station=origin,
                        alighting_station=transfer_station,
                        scheduled_departure=dep_time_a,
                        scheduled_arrival=arr_time_a,
                        scheduled_boarding_platform="1",
                        scheduled_alighting_platform="2"
                    ),
                    SegmentDTO(
                        segment_id="seg_leg_b",
                        train_number="12626",
                        boarding_station=transfer_station,
                        alighting_station=destination,
                        scheduled_departure=dep_time_b,
                        scheduled_arrival=arr_time_b,
                        scheduled_boarding_platform="4",
                        scheduled_alighting_platform="1"
                    )
                ],
                transfers=[
                    TransferDTO(
                        transfer_station=transfer_station,
                        inbound_segment_id="seg_leg_a",
                        outbound_segment_id="seg_leg_b",
                        buffer_minutes=45,
                        walking_distance_meters=150,
                        platform_change_required=True
                    )
                ],
                total_distance_km=720,
                scheduled_duration_minutes=525
            )
            candidates.append(connecting_candidate)

        return candidates
