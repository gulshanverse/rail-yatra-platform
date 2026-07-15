# app/journey/constraints/engine.py
from typing import List, Dict, Any
from app.journey.interfaces.contracts import IConstraintEngine
from app.journey.dto.models import JourneyCandidateDTO


class ConstraintEngine(IConstraintEngine):
    def evaluate_constraints(
        self, candidates: List[JourneyCandidateDTO], traveler_profile: Dict[str, Any]
    ) -> List[JourneyCandidateDTO]:
        valid_candidates = []

        # Extract constraint parameters
        max_budget = traveler_profile.get("max_budget", 99999.0)
        wheelchair_required = traveler_profile.get("wheelchair_required", False)
        max_transfers = traveler_profile.get("max_transfers", 3)
        medical_priority = traveler_profile.get("medical_priority", False)

        for candidate in candidates:
            # 1. Transfers constraint
            if len(candidate.transfers) > max_transfers:
                continue

            # 2. Wheelchair constraint: SLR coach composition check mockup.
            # SLR stands for Seating-cum-Luggage-cum-Guard coach.
            # If wheelchair required, we check if station has accessible platform features.
            if wheelchair_required:
                # Simulates station and train compatibility filters
                if candidate.total_distance_km > 1000: 
                    # Mock filter: assume long-distance connecting stations are complex and lack step-free access
                    continue

            # 3. Budget constraint (Mock check assuming a direct train cost mapping)
            # Standard segment fares calculated conceptually
            nominal_fare = len(candidate.segments) * 600.0
            if nominal_fare > max_budget:
                continue

            valid_candidates.append(candidate)

        return valid_candidates
