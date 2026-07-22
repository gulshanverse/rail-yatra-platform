"""
Automated Test Suite for Milestone 6.5 AI Memory Platform — Domain Architecture & DDD.
Verifies Aggregate Invariants, Value Objects, Domain Policies, Specifications, and State Machine.
"""

import pytest
import time

from app.memory.domain.value_objects import (
    TravelerId,
    ConfidenceScore,
    RetentionPolicy,
    BerthPreference,
    BerthPreferenceEnum,
)
from app.memory.domain.entities import (
    TravelerProfile,
    CompanionRecord,
)
from app.memory.domain.aggregates import (
    TravelerMemory,
    ConsentProfile,
    JourneySagaMemory,
)
from app.memory.domain.policies import (
    ConsentPolicy,
    ConflictResolutionPolicy,
    PrivacyPolicy,
)
from app.memory.domain.specifications import (
    ConsentGrantedSpecification,
)
from app.memory.state_machine import MemoryStateMachine, MemoryLifecycleState
from app.memory.exceptions import (
    InvariantViolationException,
    ConsentMissingException,
    ConsentWithdrawnException,
    IllegalStateTransitionException,
    SagaExpiredException,
)


def test_value_objects_validation():
    """Verify Value Objects immutability and invariant enforcement."""
    t_id = TravelerId("T1001")
    assert t_id.value == "T1001"

    with pytest.raises(InvariantViolationException):
        TravelerId("")

    score = ConfidenceScore(0.85)
    assert score.score == 0.85

    with pytest.raises(InvariantViolationException):
        ConfidenceScore(1.5)

    retention = RetentionPolicy(idle_expiration_days=365, max_age_days=730)
    assert retention.idle_expiration_days == 365

    with pytest.raises(InvariantViolationException):
        RetentionPolicy(idle_expiration_days=800, max_age_days=700)


def test_traveler_profile_and_concession():
    """Verify BR-MEM-003 Senior Concession logic on TravelerProfile entity."""
    t_id = TravelerId("T1002")
    profile = TravelerProfile(
        traveler_id=t_id, full_name="Mr. Sharma", age=67, gender="M"
    )

    assert profile.is_senior_citizen is True
    assert profile.senior_concession_eligible is True

    comp = CompanionRecord(
        name="Mrs. Sharma", age=64, gender="F", relationship="SPOUSE"
    )
    profile.add_companion(comp)
    assert len(profile.companions) == 1

    profile_dict = profile.to_dict()
    assert profile_dict["is_senior_citizen"] is True
    assert profile_dict["senior_concession_eligible"] is True


def test_consent_profile_aggregate_and_policy():
    """Verify ConsentProfile opt-in and BR-MEM-001 policy enforcement."""
    t_id = TravelerId("T1003")
    consent = ConsentProfile(traveler_id=t_id)

    assert consent.is_granted is False

    with pytest.raises(ConsentMissingException):
        ConsentPolicy.enforce_consent(consent.consent_status.status)

    consent.grant_consent(scope="FULL_PERSONALIZATION")
    assert consent.is_granted is True

    events = consent.pop_domain_events()
    assert len(events) == 1
    assert events[0].__class__.__name__ == "ConsentGrantedEvent"

    consent.withdraw_consent(reason="DPDP_RIGHT_TO_FORGET")
    assert consent.is_withdrawn is True
    with pytest.raises(ConsentWithdrawnException):
        ConsentPolicy.enforce_consent(consent.consent_status.status)


def test_traveler_memory_aggregate_invariants():
    """Verify TravelerMemory aggregate invariants and consent gates."""
    t_id = TravelerId("T1004")
    consent = ConsentProfile(traveler_id=t_id)

    # Attempt operation without active consent
    memory = TravelerMemory(traveler_id=t_id, consent_profile=consent)
    with pytest.raises(ConsentMissingException):
        memory.update_profile(full_name="Priya Consultant", age=31, gender="F")

    # Grant consent and retry
    consent.grant_consent()
    memory.update_profile(full_name="Priya Consultant", age=31, gender="F")
    assert memory.profile.full_name == "Priya Consultant"

    # Update preferences
    berth_pref = BerthPreference(BerthPreferenceEnum.WINDOW)
    memory.update_preferences(berth=berth_pref, train_class="CC", meal="VEG")
    assert memory.preferences.preferred_class == "CC"
    assert memory.preferences.berth_preference.preference == BerthPreferenceEnum.WINDOW

    events = memory.pop_domain_events()
    assert len(events) >= 2


def test_journey_saga_memory_expiration():
    """Verify JourneySagaMemory 7-day retention limit."""
    t_id = TravelerId("T1005")
    saga = JourneySagaMemory(traveler_id=t_id, origin="NDLS", destination="PUNE")
    assert saga.current_step == "INITIATED"

    saga.advance_step("TRAIN_SELECTED", {"train_number": "12626"})
    resumed = saga.resume_saga()
    assert resumed["current_step"] == "TRAIN_SELECTED"

    # Simulate expired saga (> 7 days idle)
    saga.last_active_at = time.time() - (8 * 86400)
    with pytest.raises(SagaExpiredException):
        saga.check_expiration()


def test_conflict_resolution_policy():
    """Verify recency override policy on preference conflicts."""
    old_berth = BerthPreference(BerthPreferenceEnum.LOWER)
    new_berth = BerthPreference(BerthPreferenceEnum.WINDOW)

    resolved, conflict = ConflictResolutionPolicy.resolve_preference_conflict(
        old_berth, new_berth, "berth_preference"
    )
    assert conflict is True
    assert resolved == new_berth


def test_privacy_policy_masking():
    """Verify PII data masking utilities."""
    masked_name = PrivacyPolicy.mask_pii_string("Mr. Sharma")
    assert masked_name[0] == "M"
    assert masked_name[-1] == "a"
    assert "*" in masked_name


def test_lifecycle_state_machine():
    """Verify state machine legal and illegal state transitions."""
    sm = MemoryStateMachine()
    assert sm.current_state == MemoryLifecycleState.NEW

    sm.transition_to(MemoryLifecycleState.VALIDATED)
    sm.transition_to(MemoryLifecycleState.CLASSIFIED)
    sm.transition_to(MemoryLifecycleState.ACTIVE)
    sm.transition_to(MemoryLifecycleState.UPDATED)
    sm.transition_to(MemoryLifecycleState.PURGED)

    assert sm.current_state == MemoryLifecycleState.PURGED

    # Attempt illegal transition out of terminal state PURGED
    with pytest.raises(IllegalStateTransitionException):
        sm.transition_to(MemoryLifecycleState.ACTIVE)


def test_specifications():
    """Verify Specification Pattern classes."""
    spec_consent = ConsentGrantedSpecification()
    t_id = TravelerId("T1006")
    consent = ConsentProfile(traveler_id=t_id)

    assert spec_consent.is_satisfied_by(consent) is False

    consent.grant_consent()
    assert spec_consent.is_satisfied_by(consent) is True
