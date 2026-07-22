"""
Domain Services for Milestone 6.5 AI Memory Platform.
Stateless domain services coordinating logic across aggregates and entities.
"""

from typing import Dict, Any, Optional
import time

from app.memory.domain.value_objects import (
    MemoryCategory,
)
from app.memory.domain.aggregates import TravelerMemory, ConsentProfile
from app.memory.domain.specifications import ConsentGrantedSpecification
from app.memory.exceptions import ConsentMissingException, ConsentWithdrawnException


class MemoryClassificationService:
    """Classifies interaction payloads into the enterprise memory taxonomy."""

    @staticmethod
    def classify_payload(payload: Dict[str, Any]) -> MemoryCategory:
        if "opt_in" in payload or "consent_scope" in payload:
            return MemoryCategory.CONSENT
        if "saga_id" in payload or "step" in payload:
            return MemoryCategory.SHORT_TERM
        if "berth" in payload or "meal" in payload or "train_class" in payload:
            return MemoryCategory.PREFERENCE
        if "origin" in payload and "destination" in payload and "completed" in payload:
            return MemoryCategory.JOURNEY
        if "full_name" in payload or "companion" in payload or "age" in payload:
            return MemoryCategory.LONG_TERM
        return MemoryCategory.WORKING


class MemoryConsolidationService:
    """Consolidates new choices with historical preferences."""

    @staticmethod
    def consolidate_preferences(
        memory_aggregate: TravelerMemory,
        new_preferences: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Merges new choices into the aggregate's preference store using recency resolution."""
        consolidated_changes = {}

        if "berth_preference" in new_preferences:
            berth_val = new_preferences["berth_preference"]
            memory_aggregate.update_preferences(berth=berth_val)
            consolidated_changes["berth_preference"] = str(berth_val)

        if "preferred_class" in new_preferences:
            class_val = new_preferences["preferred_class"]
            memory_aggregate.update_preferences(train_class=class_val)
            consolidated_changes["preferred_class"] = class_val

        if "meal_preference" in new_preferences:
            meal_val = new_preferences["meal_preference"]
            memory_aggregate.update_preferences(meal=meal_val)
            consolidated_changes["meal_preference"] = meal_val

        if "departure_window" in new_preferences:
            window_val = new_preferences["departure_window"]
            memory_aggregate.update_preferences(window=window_val)
            consolidated_changes["departure_window"] = window_val

        return consolidated_changes


class ConsentEvaluationService:
    """Verifies consent status before executing memory recall or persistence operations."""

    def __init__(self):
        self.spec = ConsentGrantedSpecification()

    def verify_consent(self, consent_profile: Optional[ConsentProfile]) -> bool:
        if consent_profile is None:
            raise ConsentMissingException(
                "BR-MEM-001: No ConsentProfile associated with candidate."
            )
        if consent_profile.is_withdrawn:
            raise ConsentWithdrawnException(
                "BR-MEM-001: Traveler consent has been WITHDRAWN."
            )
        if not consent_profile.is_granted:
            raise ConsentMissingException("BR-MEM-001: Consent status is not GRANTED.")
        return True


class MemoryQualityService:
    """Calculates accuracy, freshness, and completeness metrics for stored memories."""

    @staticmethod
    def calculate_memory_quality(
        memory_aggregate: TravelerMemory,
    ) -> Dict[str, Any]:
        now = time.time()
        last_active = memory_aggregate.last_active_at
        idle_days = (now - last_active) / 86400.0

        # Freshness metric: 1.0 if active today, decaying over 365 days
        freshness = max(0.0, 1.0 - (idle_days / 365.0))

        # Completeness metric based on profile and preference population
        profile = memory_aggregate.profile
        prefs = memory_aggregate.preferences

        has_name = (
            1.0
            if profile.full_name and profile.full_name != "Unregistered Traveler"
            else 0.0
        )
        has_age = 1.0 if profile.age > 0 else 0.0
        has_pref = 1.0 if prefs.preferred_class else 0.0
        has_history = 1.0 if len(memory_aggregate.journey_history.routes) > 0 else 0.5

        completeness = (has_name + has_age + has_pref + has_history) / 4.0

        # Overall quality score
        quality_score = round((freshness * 0.4) + (completeness * 0.6), 2)

        return {
            "freshness_score": round(freshness, 2),
            "completeness_score": round(completeness, 2),
            "overall_quality_score": quality_score,
        }


class MemoryPurgeService:
    """Executes Right-to-be-Forgotten purges across memory aggregates."""

    @staticmethod
    def execute_purge(
        memory_aggregate: TravelerMemory,
        consent_profile: ConsentProfile,
        reason: str = "USER_RIGHT_TO_BE_FORGOTTEN",
    ) -> int:
        consent_profile.withdraw_consent(reason=reason)
        purged_count = memory_aggregate.purge_all_memory()
        return purged_count
