# app/tests/test_intelligence_platform.py
import pytest
import time
from unittest.mock import AsyncMock
from app.integration.interfaces import NormalizedResponse
from app.integration.models import TrainStatusResponse, PNRStatusResponse
from app.intelligence import (
    DomainValidator,
    NormalizationEngine,
    BusinessRuleEngine,
    ConfidenceEngine,
    FreshnessEngine,
    ProvenanceEngine,
    ConflictResolutionEngine,
    DerivedIntelligenceEngine,
    RailwayEventEngine,
    OntologyManager,
    MetadataManager,
    LanguageManager,
    RailwayIntelligenceGateway,
)

# ==========================================
# Component Unit Tests
# ==========================================


def test_validator():
    validator = DomainValidator()
    # Train
    assert validator.validate_train_number("12002") is True
    assert validator.validate_train_number("1200") is False
    assert validator.validate_train_number("abcde") is False

    # Station
    assert validator.validate_station_code("NDLS") is True
    assert validator.validate_station_code("ndls") is True  # strip and upper inside
    assert validator.validate_station_code("ND") is False
    assert validator.validate_station_code("NDLSS") is True

    # PNR
    assert validator.validate_pnr("4321098765") is True
    assert validator.validate_pnr("9321098765") is False  # first digit check
    assert validator.validate_pnr("432109876") is False

    # Coach & Platform
    assert validator.validate_coach_label("S1") is True
    assert validator.validate_platform_number("PF-1A") is True

    # Date — use a dynamically computed future date so the test is time-resilient
    from datetime import datetime, timedelta

    future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    assert validator.validate_date(future_date) is True
    assert validator.validate_date("invalid-date") is False


def test_normalizer():
    normalizer = NormalizationEngine()
    # Station aliases
    assert normalizer.normalize_station_code("New Delhi") == "NDLS"
    assert normalizer.normalize_station_code("नई दिल्ली") == "NDLS"
    assert normalizer.normalize_station_code("unknown") == "UNKNOWN"

    # Delay minutes parser
    assert normalizer.normalize_delay(15) == 15
    assert normalizer.normalize_delay("15 mins") == 15
    assert normalizer.normalize_delay("1 hour 15 mins") == 75
    assert normalizer.normalize_delay("02:15") == 135
    assert normalizer.normalize_delay("none") == 0

    # Class codes
    assert normalizer.normalize_class_code("3AC") == "3A"
    assert normalizer.normalize_class_code("AC 3-Tier") == "3A"
    assert normalizer.normalize_class_code("Sleeper") == "SL"

    # Platforms and Quotas
    assert normalizer.normalize_platform_number("PF-12") == "12"
    assert normalizer.normalize_platform_number("Platform 2") == "2"
    assert normalizer.normalize_quota_code("Tatkal") == "TQ"


def test_business_rules():
    rules = BusinessRuleEngine()
    # Refund calculations
    assert rules.evaluate_refund_policy("CANCELLED", "3A", 10, 1000.0) == 1000.0
    assert (
        rules.evaluate_refund_policy("ACTIVE", "3A", 50, 1000.0) == 820.0
    )  # 1000 - 180 flat
    assert (
        rules.evaluate_refund_policy("ACTIVE", "3A", 20, 1000.0) == 750.0
    )  # 25% charge
    assert (
        rules.evaluate_refund_policy("ACTIVE", "3A", 6, 1000.0) == 500.0
    )  # 50% charge
    assert rules.evaluate_refund_policy("ACTIVE", "3A", 2, 1000.0) == 0.0  # < 4 hours

    # Tatkal hour checks
    assert rules.is_tatkal_window_active("3A", "10:30") is True
    assert rules.is_tatkal_window_active("3A", "11:30") is False
    assert rules.is_tatkal_window_active("SL", "11:15") is True
    assert rules.is_tatkal_window_active("SL", "10:15") is False


def test_confidence_and_freshness():
    confidence = ConfidenceEngine()
    assert confidence.calculate_confidence("cris", 0.0, True) == 100.0
    assert confidence.calculate_confidence("confirmtkt", 300.0, False) < 95.0

    freshness = FreshnessEngine()
    assert freshness.is_stale("live_train_status", 120.0) is True
    assert freshness.is_stale("live_train_status", 30.0) is False
    assert freshness.get_max_age_seconds("schedule") == 2592000.0


def test_provenance_and_metadata():
    provenance = ProvenanceEngine()
    p_log = provenance.record_provenance("cris", "1.0", "pip", "1.0", "VALID")
    assert p_log["original_provider"] == "cris"
    assert "processing_timestamp" in p_log

    meta = MetadataManager()
    encrypted = meta.encrypt_pii("Gulshan Kumar")
    assert encrypted != "Gulshan Kumar"
    assert meta.decrypt_pii(encrypted) == "Gulshan Kumar"


def test_conflict_resolution():
    conflict = ConflictResolutionEngine()
    delays = [
        {"delay_minutes": 10, "provider_id": "confirmtkt", "sync_timestamp": 100.0},
        {
            "delay_minutes": 20,
            "provider_id": "cris",
            "sync_timestamp": 101.0,
            "is_official_source": True,
        },
    ]
    assert conflict.resolve_delay_conflict(delays) == 20

    platforms = [
        {"platform_number": "1", "provider_id": "confirmtkt", "sync_timestamp": 100.0},
        {
            "platform_number": "2",
            "provider_id": "ntes",
            "sync_timestamp": 101.0,
            "is_official_source": True,
        },
    ]
    assert conflict.resolve_platform_conflict(platforms) == "2"


def test_derived_intelligence():
    derived = DerivedIntelligenceEngine()
    # Journey connections risk
    assert (
        derived.calculate_journey_risk(30, 45, 10) == "HIGH"
    )  # tightening buffer (15m left)
    assert derived.calculate_journey_risk(10, 45, 10) == "LOW"
    assert derived.calculate_journey_risk(20, 45, 20) == "MEDIUM"

    # Platform stability
    assert (
        derived.calculate_platform_stability("NDLS", "12002") == 0.80
    )  # premium but busy station
    assert derived.calculate_platform_stability("AGC", "12001") == 0.80


def test_ontology_and_language():
    ontology = OntologyManager()
    assert ontology.get_zone_for_division("DLI") == "NR"
    assert ontology.get_division_for_station("NDLS") == "DLI"

    spatial = ontology.get_spatial_hierarchy("NDLS")
    assert spatial["zone"] == "NR"
    assert spatial["station"] == "NDLS"

    lang = LanguageManager()
    assert lang.transliterate_to_english("नई दिल्ली") == "NEW DELHI"
    assert lang.get_localized_name("NDLS", "hi") == "नई दिल्ली"


# ==========================================
# Integration & Mock Gateway Tests
# ==========================================


@pytest.mark.anyio
async def test_intelligence_gateway_train_flow():
    # Setup integration mocks
    mock_integ = AsyncMock()

    train_dto = TrainStatusResponse(
        train_number="12002",
        train_name="Shatabdi Express",
        current_station="AGC",
        last_updated=time.time(),
        delay_minutes=15,
        route_movements=[],
    )

    mock_integ.execute.return_value = NormalizedResponse(
        success=True, provider_id="cris", latency_ms=10.0, data=train_dto.model_dump()
    )

    # Initialize gateway with dependencies
    gateway = RailwayIntelligenceGateway(
        integration_gateway=mock_integ,
        validator=DomainValidator(),
        normalizer=NormalizationEngine(),
        rule_engine=BusinessRuleEngine(),
        confidence_engine=ConfidenceEngine(),
        freshness_engine=FreshnessEngine(),
        provenance_engine=ProvenanceEngine(),
        conflict_resolver=ConflictResolutionEngine(),
        derived_engine=DerivedIntelligenceEngine(),
        event_engine=RailwayEventEngine(),
        ontology_manager=OntologyManager(),
        metadata_manager=MetadataManager(),
    )

    context = await gateway.get_train_intelligence(
        train_number="12002", boarding_station="NDLS"
    )

    assert context.domain_type == "JourneyCanonical"
    assert context.canonical_data["resolved_delay_minutes"] == 15
    assert context.canonical_data["journey_risk"] == "LOW"
    assert context.metadata["confidence_score"] == 99.17


@pytest.mark.anyio
async def test_intelligence_gateway_pnr_flow():
    mock_integ = AsyncMock()

    pnr_dto = PNRStatusResponse(
        pnr="4321098765",
        train_number="12002",
        train_name="Shatabdi",
        journey_date="2026-07-20",
        booking_class="3AC",
        chart_status="UNCHARTED",
        passengers=[
            {
                "passenger_number": 1,
                "booking_status": "WL 10",
                "current_status": "RAC 2",
            }
        ],
    )

    mock_integ.execute.return_value = NormalizedResponse(
        success=True,
        provider_id="confirmtkt_gds",
        latency_ms=15.0,
        data=pnr_dto.model_dump(),
    )

    gateway = RailwayIntelligenceGateway(
        integration_gateway=mock_integ,
        validator=DomainValidator(),
        normalizer=NormalizationEngine(),
        rule_engine=BusinessRuleEngine(),
        confidence_engine=ConfidenceEngine(),
        freshness_engine=FreshnessEngine(),
        provenance_engine=ProvenanceEngine(),
        conflict_resolver=ConflictResolutionEngine(),
        derived_engine=DerivedIntelligenceEngine(),
        event_engine=RailwayEventEngine(),
        ontology_manager=OntologyManager(),
        metadata_manager=MetadataManager(),
    )

    context = await gateway.get_pnr_intelligence(pnr_number="4321098765")

    assert context.domain_type == "PNRCanonical"
    assert context.canonical_data["pnr_number"] == "4321098765"
    assert context.canonical_data["booking_class"] == "3A"
    assert len(context.canonical_data["passengers"]) == 1
