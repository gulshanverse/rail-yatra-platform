"""
Composition Lifecycle State Machine for Milestone 6.6 AI Response Composer & Explainability Platform.
Enforces legal and illegal state transitions across response synthesis lifecycles.
"""

from enum import Enum
from typing import Dict, Set, List, Tuple
import time

from app.composer.exceptions import IllegalCompositionStateTransition


class CompositionState(str, Enum):
    """Enterprise Response Composition Lifecycle States."""

    INITIATED = "INITIATED"
    CONTEXT_GATHERED = "CONTEXT_GATHERED"
    ARBITRATED = "ARBITRATED"
    EXPLAINED = "EXPLAINED"
    PRIVACY_CHECKED = "PRIVACY_CHECKED"
    COMPOSED = "COMPOSED"
    VALIDATED = "VALIDATED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class CompositionStateMachine:
    """State machine governing execution phase transitions for response composition."""

    ALLOWED_TRANSITIONS: Dict[CompositionState, Set[CompositionState]] = {
        CompositionState.INITIATED: {
            CompositionState.CONTEXT_GATHERED,
            CompositionState.FAILED,
        },
        CompositionState.CONTEXT_GATHERED: {
            CompositionState.ARBITRATED,
            CompositionState.FAILED,
        },
        CompositionState.ARBITRATED: {
            CompositionState.EXPLAINED,
            CompositionState.FAILED,
        },
        CompositionState.EXPLAINED: {
            CompositionState.PRIVACY_CHECKED,
            CompositionState.FAILED,
        },
        CompositionState.PRIVACY_CHECKED: {
            CompositionState.COMPOSED,
            CompositionState.FAILED,
        },
        CompositionState.COMPOSED: {
            CompositionState.VALIDATED,
            CompositionState.FAILED,
        },
        CompositionState.VALIDATED: {
            CompositionState.DELIVERED,
            CompositionState.FAILED,
        },
        CompositionState.DELIVERED: set(),  # Terminal state: success
        CompositionState.FAILED: set(),     # Terminal state: failure
    }

    def __init__(self, initial_state: CompositionState = CompositionState.INITIATED):
        self._current_state = initial_state
        self.state_history: List[Tuple[CompositionState, float]] = [(initial_state, time.time())]

    @property
    def current_state(self) -> CompositionState:
        return self._current_state

    def transition_to(self, target_state: CompositionState) -> CompositionState:
        if self._current_state in (CompositionState.DELIVERED, CompositionState.FAILED):
            raise IllegalCompositionStateTransition(
                f"ILLEGAL TRANSITION: Cannot transition out of terminal state {self._current_state.value} to {target_state.value}."
            )

        allowed = self.ALLOWED_TRANSITIONS.get(self._current_state, set())
        if target_state not in allowed:
            raise IllegalCompositionStateTransition(
                f"Invalid Composition Transition: {self._current_state.value} -> {target_state.value} is prohibited."
            )

        self._current_state = target_state
        self.state_history.append((target_state, time.time()))
        return self._current_state
