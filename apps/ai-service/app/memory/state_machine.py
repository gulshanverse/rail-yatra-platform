"""
Lifecycle State Machine for Milestone 6.5 AI Memory Platform.
Enforces legal and illegal state transitions across memory entry lifecycles.
"""

from enum import Enum
from typing import Dict, Set
import time

from app.memory.exceptions import IllegalStateTransitionException


class MemoryLifecycleState(str, Enum):
    """Enterprise Memory Lifecycle States."""

    NEW = "NEW"
    VALIDATED = "VALIDATED"
    CLASSIFIED = "CLASSIFIED"
    ACTIVE = "ACTIVE"
    UPDATED = "UPDATED"
    RECALLED = "RECALLED"
    CONSOLIDATED = "CONSOLIDATED"
    EXPIRED = "EXPIRED"
    PURGED = "PURGED"


class MemoryStateMachine:
    """State machine governing state transitions for memory entries."""

    # Transition matrix defining allowed target states for each current state
    ALLOWED_TRANSITIONS: Dict[MemoryLifecycleState, Set[MemoryLifecycleState]] = {
        MemoryLifecycleState.NEW: {
            MemoryLifecycleState.VALIDATED,
            MemoryLifecycleState.PURGED,
        },
        MemoryLifecycleState.VALIDATED: {
            MemoryLifecycleState.CLASSIFIED,
            MemoryLifecycleState.PURGED,
        },
        MemoryLifecycleState.CLASSIFIED: {
            MemoryLifecycleState.ACTIVE,
            MemoryLifecycleState.PURGED,
        },
        MemoryLifecycleState.ACTIVE: {
            MemoryLifecycleState.UPDATED,
            MemoryLifecycleState.RECALLED,
            MemoryLifecycleState.CONSOLIDATED,
            MemoryLifecycleState.EXPIRED,
            MemoryLifecycleState.PURGED,
        },
        MemoryLifecycleState.UPDATED: {
            MemoryLifecycleState.ACTIVE,
            MemoryLifecycleState.RECALLED,
            MemoryLifecycleState.CONSOLIDATED,
            MemoryLifecycleState.EXPIRED,
            MemoryLifecycleState.PURGED,
        },
        MemoryLifecycleState.RECALLED: {
            MemoryLifecycleState.ACTIVE,
            MemoryLifecycleState.UPDATED,
            MemoryLifecycleState.CONSOLIDATED,
            MemoryLifecycleState.EXPIRED,
            MemoryLifecycleState.PURGED,
        },
        MemoryLifecycleState.CONSOLIDATED: {
            MemoryLifecycleState.ACTIVE,
            MemoryLifecycleState.UPDATED,
            MemoryLifecycleState.RECALLED,
            MemoryLifecycleState.EXPIRED,
            MemoryLifecycleState.PURGED,
        },
        MemoryLifecycleState.EXPIRED: {MemoryLifecycleState.PURGED},
        MemoryLifecycleState.PURGED: set(),  # Terminal state: zero allowed transitions!
    }

    def __init__(self, initial_state: MemoryLifecycleState = MemoryLifecycleState.NEW):
        self._current_state = initial_state
        self.state_history = [(initial_state, time.time())]

    @property
    def current_state(self) -> MemoryLifecycleState:
        return self._current_state

    def transition_to(self, target_state: MemoryLifecycleState) -> MemoryLifecycleState:
        if self._current_state == MemoryLifecycleState.PURGED:
            raise IllegalStateTransitionException(
                f"ILLEGAL TRANSITION: Cannot transition out of terminal state PURGED to {target_state.value}."
            )

        allowed = self.ALLOWED_TRANSITIONS.get(self._current_state, set())
        if target_state not in allowed:
            raise IllegalStateTransitionException(
                f"Invalid State Transition: {self._current_state.value} -> {target_state.value} is prohibited."
            )

        self._current_state = target_state
        self.state_history.append((target_state, time.time()))
        return self._current_state
