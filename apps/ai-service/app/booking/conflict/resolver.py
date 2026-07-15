# app/booking/conflict/resolver.py
from typing import List, Dict, Any
from app.booking.interfaces.contracts import IConflictResolutionEngine


class ConflictResolver(IConflictResolutionEngine):
    def resolve_conflicts(
        self, candidates: List[Any], profile: Dict[str, Any]
    ) -> List[Any]:
        # Resolves strategy choices conflicts:
        # e.g., if budget cap is tight and Tatkal premium is high, prunes Tatkal candidates
        resolved = []
        max_budget = profile.get("max_budget", 99999.0)

        for candidate in candidates:
            # Conflict Check: Tatkal premium pricing versus budget caps
            if (
                candidate.candidate.selected_quota == "PT"
                and candidate.candidate.estimated_fare > max_budget
            ):
                # Discard conflicting option
                continue

            resolved.append(candidate)

        return resolved
