# app/traveler/context/factory.py
"""
Standalone context factory module.

Delegates to the canonical TravelerDecisionContextFactory defined in
``gateway.coordinator`` so that both import paths resolve to the same
implementation.  This module exists to match the package layout specified
in the Planning document (§3 – ``context/factory.py``).
"""

from app.traveler.gateway.coordinator import (
    TravelerDecisionContext,
    TravelerDecisionContextFactory,
)

__all__ = [
    "TravelerDecisionContext",
    "TravelerDecisionContextFactory",
]
