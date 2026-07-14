"""
Conflict resolution strategies (Reject, Overwrite) and mapping definitions.
"""

from typing import Any
from app.memory.versioning import MemoryVersionConflict

STRATEGY_REJECT = "REJECT"
STRATEGY_OVERWRITE = "OVERWRITE"


class ConflictResolver:
    """Orchestrates resolution behavior when concurrent conflicts occur."""

    @staticmethod
    def resolve(
        current_data: Any, incoming_data: Any, strategy: str = STRATEGY_REJECT
    ) -> Any:
        """
        Determines conflict resolution outcome.
        Returns:
            incoming_data if OVERWRITE
            Raises MemoryVersionConflict if REJECT
        """
        if strategy == STRATEGY_REJECT:
            raise MemoryVersionConflict(
                "Conflict Resolution Policy: Rejecting stale write."
            )
        elif strategy == STRATEGY_OVERWRITE:
            return incoming_data
        else:
            raise ValueError(f"Unknown conflict resolution strategy: {strategy}")
