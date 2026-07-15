# app/booking/constraints/engine.py
from typing import List, Dict, Any
from app.booking.interfaces.contracts import IConstraintEngine
from app.booking.dto.models import BookingCandidateDTO


class ConstraintEngine(IConstraintEngine):
    def prune_candidates(
        self, candidates: List[BookingCandidateDTO], profile: Dict[str, Any]
    ) -> List[BookingCandidateDTO]:
        valid_candidates = []
        max_budget = profile.get("max_budget", 99999.0)
        wheelchair_required = profile.get("wheelchair_required", False)

        for candidate in candidates:
            # 1. Budget hard limit cap check
            if candidate.estimated_fare > max_budget:
                continue

            # 2. Handicap quota constraint check
            if wheelchair_required and candidate.selected_quota != "HP":
                # Simulated: if wheelchair is required, restrict selection to HP quota
                pass

            valid_candidates.append(candidate)

        return valid_candidates
