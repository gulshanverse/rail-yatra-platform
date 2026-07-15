# app/intelligence/models.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ==========================================
# Metadata & Lineage Schemas
# ==========================================
class CanonicalMetadata(BaseModel):
    source_provider: str = Field(
        ..., description="Unique provider ID (e.g. 'confirmtkt_gds')"
    )
    sync_timestamp: float = Field(
        ..., description="Epoch timestamp when the data was retrieved."
    )
    confidence_score: float = Field(
        ..., description="Data confidence rating (0.0 to 100.0)."
    )
    data_freshness_seconds: float = Field(
        ..., description="Elapsed time since retrieval."
    )
    api_schema_version: str = Field(
        "1.0.0", description="Version of the source API schema."
    )
    jurisdiction: str = Field("IN", description="Geographic zone code.")


class ProvenanceMetadata(BaseModel):
    original_provider: str
    provider_version: str
    transformation_pipeline_id: str
    normalization_version: str
    validation_status: str
    processing_timestamp: float


# ==========================================
# Canonical Domain Entities
# ==========================================
class ZoneCanonical(BaseModel):
    zone_code: str
    zone_name: str
    headquarters: str


class DivisionCanonical(BaseModel):
    division_code: str
    division_name: str
    zone_code: str


class StationCanonical(BaseModel):
    station_code: str
    station_name: str
    latitude: float
    longitude: float
    platform_count: int
    division: str
    zone: str


class TrainCanonical(BaseModel):
    train_number: str = Field(..., min_length=5, max_length=5)
    train_name: str
    category: str
    runs_on_days: List[str]
    source_station_code: str
    destination_station_code: str


class ScheduleStation(BaseModel):
    station_code: str
    arrival_time: str
    departure_time: str
    distance_km: int
    day_number: int


class ScheduleCanonical(BaseModel):
    train_number: str
    stops: List[ScheduleStation]


class JourneyCanonical(BaseModel):
    journey_id: str
    train_number: str
    journey_date: str
    departure_time: str
    arrival_time: str
    status: str


class PassengerCanonical(BaseModel):
    passenger_number: int
    booking_status: str
    current_status: str
    coach_id: Optional[str] = None
    seat_number: Optional[int] = None


class PNRCanonical(BaseModel):
    pnr_number: str
    train_number: str
    journey_date: str
    booking_class: str
    chart_status: str
    passengers: List[PassengerCanonical]


class CoachCanonical(BaseModel):
    coach_id: str
    class_type: str
    position_from_engine: int


class PlatformCanonical(BaseModel):
    train_number: str
    station_code: str
    scheduled_platform: str
    actual_platform: Optional[str] = None


class QuotaCanonical(BaseModel):
    quota_code: str
    quota_name: str


class FareCanonical(BaseModel):
    train_number: str
    source: str
    destination: str
    class_code: str
    base_fare: float
    catering_charge: float
    tax: float
    total_fare: float


class DelayCanonical(BaseModel):
    train_number: str
    station_code: str
    delay_minutes: int


class CancellationCanonical(BaseModel):
    train_number: str
    cancellation_type: str
    cancellation_reason: str
    effective_date: str


class AlertCanonical(BaseModel):
    alert_id: str
    alert_title: str
    severity: str
    description: str
    expiry_time: float


class CompositionCanonical(BaseModel):
    train_number: str
    coaches: List[CoachCanonical]
    total_coaches: int


class TravelEventCanonical(BaseModel):
    event_id: str
    event_type: str
    priority: int
    severity: str
    payload: Dict[str, Any]
    timestamp: float


# ==========================================
# AI Target Output Context
# ==========================================
class AIReadyContext(BaseModel):
    domain_type: str
    canonical_data: Dict[str, Any]
    metadata: Dict[str, Any]
