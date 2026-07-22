"""
Automated Test Suite for Milestone 6.5 AI Memory Platform — Application Layer & CQRS.
Verifies Use Cases UC-MEM-01, UC-MEM-02, UC-MEM-03, Consent Management, Right-to-be-Forgotten Purges, CQRS, and Governance.
"""

import pytest

from app.memory.application.services import (
    ConsentApplicationService,
    MemoryApplicationService,
    JourneySagaApplicationService,
    MemoryGovernanceApplicationService,
)
from app.memory.domain.repositories import (
    InMemoryConsentProfileRepository,
    InMemoryTravelerMemoryRepository,
    InMemoryJourneySagaRepository,
    InMemoryAuditLogger,
)
from app.memory.domain.value_objects import TravelerId
from app.memory.domain.aggregates import JourneySagaMemory
from app.memory.exceptions import ConsentMissingException


def test_use_case_uc_mem_01_store_profile():
    """Verify UC-MEM-01: Store Passenger Profile details with consent gate."""
    consent_repo = InMemoryConsentProfileRepository()
    audit_logger = InMemoryAuditLogger()
    memory_repo = InMemoryTravelerMemoryRepository(consent_repo=consent_repo)

    consent_svc = ConsentApplicationService(consent_repo, memory_repo, audit_logger)
    memory_svc = MemoryApplicationService(memory_repo, consent_repo, audit_logger)

    traveler_id = "T_SHARMA_67"

    # Step 1: Attempt to store profile without consent -> fails
    with pytest.raises(ConsentMissingException):
        memory_svc.store_traveler_profile(
            traveler_id=traveler_id,
            full_name="Mr. Sharma",
            age=67,
            gender="M",
        )

    # Step 2: Grant explicit opt-in consent
    grant_res = consent_svc.grant_consent(traveler_id=traveler_id)
    assert grant_res["status"] == "SUCCESS"
    assert grant_res["consent_status"] == "GRANTED"

    # Step 3: Store profile with companion
    res = memory_svc.store_traveler_profile(
        traveler_id=traveler_id,
        full_name="Mr. Sharma",
        age=67,
        gender="M",
        companion_name="Mrs. Sharma",
        companion_age=64,
        companion_gender="F",
    )
    assert res["status"] == "SUCCESS"
    profile_data = res["memory"]["profile"]
    assert profile_data["full_name"] == "Mr. Sharma"
    assert profile_data["is_senior_citizen"] is True
    assert profile_data["senior_concession_eligible"] is True
    assert len(profile_data["companions"]) == 1


def test_use_case_uc_mem_02_auto_fill_parameters():
    """Verify UC-MEM-02: Auto-Fill Booking Parameters with consent filtering."""
    consent_repo = InMemoryConsentProfileRepository()
    audit_logger = InMemoryAuditLogger()
    memory_repo = InMemoryTravelerMemoryRepository(consent_repo=consent_repo)

    consent_svc = ConsentApplicationService(consent_repo, memory_repo, audit_logger)
    memory_svc = MemoryApplicationService(memory_repo, consent_repo, audit_logger)

    traveler_id = "T_PRIYA_31"

    # Unconsented query returns zero-knowledge projection
    auto_fill_unconsented = memory_svc.auto_fill_booking_parameters(traveler_id)
    assert auto_fill_unconsented["has_consent"] is False
    assert auto_fill_unconsented["profile"] is None

    # Opt in and set preferences
    consent_svc.grant_consent(traveler_id)
    memory_svc.store_traveler_profile(traveler_id, "Priya Consultant", 31, "F")
    memory_svc.update_preferences(
        traveler_id=traveler_id,
        berth_preference="WINDOW",
        preferred_class="CC",
        meal_preference="VEG",
        departure_window="EVENING",
    )

    # Consented query returns preferences for auto-fill
    auto_fill_res = memory_svc.auto_fill_booking_parameters(traveler_id)
    assert auto_fill_res["has_consent"] is True
    prefs = auto_fill_res["preferences"]
    assert prefs["preferred_class"] == "CC"
    assert prefs["berth_preference"] == "WINDOW"


def test_use_case_uc_mem_03_resume_booking_saga():
    """Verify UC-MEM-03: Resume Interrupted Booking Saga across sessions."""
    saga_repo = InMemoryJourneySagaRepository()
    audit_logger = InMemoryAuditLogger()
    saga_svc = JourneySagaApplicationService(saga_repo, audit_logger)

    traveler_id = "T_PRIYA_31"
    t_id = TravelerId(traveler_id)

    # Initiate active booking saga
    saga = JourneySagaMemory(
        traveler_id=t_id,
        origin="NDLS",
        destination="PUNE",
        current_step="PAYMENT_PENDING",
        step_data={"train_no": "12626", "passengers": ["Priya Consultant"]},
    )
    saga_repo.save(saga)

    # Interrupted session returns active saga context
    ctx_res = saga_svc.get_recent_context(traveler_id)
    assert ctx_res["has_active_saga"] is True
    assert ctx_res["saga"]["current_step"] == "PAYMENT_PENDING"

    # Resume saga workflow
    resume_res = saga_svc.resume_booking_saga(
        saga_id=saga.saga_id, traveler_id=traveler_id
    )
    assert resume_res["status"] == "SUCCESS"
    assert resume_res["saga"]["origin"] == "NDLS"
    assert resume_res["saga"]["destination"] == "PUNE"


def test_right_to_be_forgotten_purge():
    """Verify Right-to-be-Forgotten consent withdrawal and aggregate purging."""
    consent_repo = InMemoryConsentProfileRepository()
    audit_logger = InMemoryAuditLogger()
    memory_repo = InMemoryTravelerMemoryRepository(consent_repo=consent_repo)

    consent_svc = ConsentApplicationService(consent_repo, memory_repo, audit_logger)
    memory_svc = MemoryApplicationService(memory_repo, consent_repo, audit_logger)
    gov_svc = MemoryGovernanceApplicationService(memory_repo, audit_logger)

    traveler_id = "T_SHARMA_67"
    consent_svc.grant_consent(traveler_id)
    memory_svc.store_traveler_profile(traveler_id, "Mr. Sharma", 67, "M")

    # Execute Right-to-be-Forgotten purge
    purge_res = consent_svc.withdraw_consent(traveler_id, reason="DPDP_RIGHT_TO_FORGET")
    assert purge_res["status"] == "SUCCESS"
    assert purge_res["records_purged"] > 0

    # Verify query returns zero-knowledge state
    auto_fill_res = memory_svc.auto_fill_booking_parameters(traveler_id)
    assert auto_fill_res["has_consent"] is False

    # Verify audit log captures purge action
    audit_res = gov_svc.get_memory_audit_trail(traveler_id)
    assert audit_res["audit_count"] > 0
    actions = [e["action"] for e in audit_res["trail"]]
    assert "WITHDRAW_CONSENT_PURGE" in actions


def test_governance_quality_metrics():
    """Verify Memory Governance Application Service quality score calculation."""
    consent_repo = InMemoryConsentProfileRepository()
    audit_logger = InMemoryAuditLogger()
    memory_repo = InMemoryTravelerMemoryRepository(consent_repo=consent_repo)

    consent_svc = ConsentApplicationService(consent_repo, memory_repo, audit_logger)
    memory_svc = MemoryApplicationService(memory_repo, consent_repo, audit_logger)
    gov_svc = MemoryGovernanceApplicationService(memory_repo, audit_logger)

    traveler_id = "T_QUALITY_1"
    consent_svc.grant_consent(traveler_id)
    memory_svc.store_traveler_profile(traveler_id, "Quality User", 35, "M")
    memory_svc.update_preferences(traveler_id, preferred_class="1AC", meal="VEG")

    quality_res = gov_svc.get_memory_quality(traveler_id)
    assert quality_res["overall_quality_score"] > 0.5
    assert quality_res["completeness_score"] > 0.5


def test_telemetry_and_config():
    """Verify MemoryConfig and telemetry metrics recording functions."""
    from app.memory.config import default_memory_config
    from app.memory.telemetry import telemetry_collector

    # Config validation
    assert default_memory_config.idle_expiration_days == 365
    assert default_memory_config.saga_max_retention_days == 7

    # Telemetry registration validation
    telemetry_collector.record_metric("query_hits_total", 5)
    telemetry_collector.record_span("GET_CONTEXT", "T_TEST", "SUCCESS", 12.5)

    summary = telemetry_collector.get_metrics_summary()
    assert summary["counters"]["query_hits_total"] == 5
    assert summary["total_spans_recorded"] > 0
