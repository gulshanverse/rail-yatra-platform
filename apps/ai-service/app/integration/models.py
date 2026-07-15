# app/integration/models.py
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


# ==========================================
# Authentication & Registry Schemas
# ==========================================
class RateLimitConfig(BaseModel):
    requests_per_minute: int
    burst_limit: int
    daily_quota: int
    monthly_budget_usd: float


class ProviderMetadata(BaseModel):
    provider_id: str = Field(
        ..., description="Unique provider ID (e.g. 'confirmtkt_gds')"
    )
    name: str
    version: str
    status: str = Field("active", description="active, deprecated, offline")
    capabilities: List[str] = Field(
        ..., description="e.g. ['pnr_lookup', 'coach_position']"
    )
    auth_method: str = Field(..., description="oauth2, apikey, mtls, none")
    rate_limits: RateLimitConfig
    sla_availability: float = Field(
        0.999, description="Contracted availability target (0.0 to 1.0)"
    )
    expected_latency_ms: int
    cost_per_query_usd: float
    priority: int = Field(
        1, description="Primary routing hierarchy weight (lower is higher priority)"
    )
    region: str = Field("IN", description="Geographic zone of the provider")
    owner: str = Field("IntegrationTeam", description="Operational owner tag")
    lifecycle_stage: str = Field(
        "production", description="candidate, evaluation, production, retired"
    )


# ==========================================
# Request Correlation Context
# ==========================================
class CorrelationContext(BaseModel):
    correlation_id: str
    request_id: str
    trace_id: str
    session_id: Optional[str] = None


# ==========================================
# 8.1 PNR Status Interface DTO
# ==========================================
class PassengerStatus(BaseModel):
    passenger_number: int
    booking_status: str
    current_status: str


class PNRStatusResponse(BaseModel):
    pnr: str = Field(..., min_length=10, max_length=10)
    train_number: str
    train_name: str
    journey_date: str
    booking_class: str
    chart_status: str
    passengers: List[PassengerStatus]
    confirmation_probability: Optional[str] = None
    delay_prediction: Optional[str] = None


# ==========================================
# 8.2 Live Train Status Interface DTO
# ==========================================
class StationMovement(BaseModel):
    station_code: str
    station_name: str
    scheduled_arrival: str
    actual_arrival: str
    scheduled_departure: str
    actual_departure: str
    delay_minutes: int
    status: str


class TrainStatusResponse(BaseModel):
    train_number: str
    train_name: str
    current_station: str
    last_updated: float
    delay_minutes: int
    route_movements: List[StationMovement]


# ==========================================
# 8.3 Train Schedule Interface DTO
# ==========================================
class ScheduleStation(BaseModel):
    station_code: str
    arrival_time: str
    departure_time: str
    distance_km: int
    day_number: int


class TrainScheduleResponse(BaseModel):
    train_number: str
    train_name: str
    runs_on: List[str]
    stations: List[ScheduleStation]


# ==========================================
# 8.4 Station Information Interface DTO
# ==========================================
class StationInfoResponse(BaseModel):
    station_code: str
    station_name: str
    division: str
    zone: str
    latitude: float
    longitude: float
    platform_count: int


# ==========================================
# 8.5 Coach Position Interface DTO
# ==========================================
class CoachLayout(BaseModel):
    coach_id: str
    class_type: str
    position_from_engine: int


class CoachPositionResponse(BaseModel):
    train_number: str
    coaches: List[CoachLayout]
    total_coaches: int


# ==========================================
# 8.6 Platform Information Interface DTO
# ==========================================
class PlatformInfoResponse(BaseModel):
    train_number: str
    station_code: str
    scheduled_platform: str
    actual_platform: Optional[str] = None


# ==========================================
# 8.7 Seat Availability Interface DTO
# ==========================================
class AvailabilityDate(BaseModel):
    date: str
    status: str
    probability: Optional[float] = None


class SeatAvailabilityResponse(BaseModel):
    train_number: str
    source: str
    destination: str
    quota: str
    booking_class: str
    availability: List[AvailabilityDate]


# ==========================================
# 8.8 Fare Inquiry Interface DTO
# ==========================================
class ClassFare(BaseModel):
    class_code: str
    base_fare: float
    catering_charge: float
    tax: float
    total_fare: float


class FareInquiryResponse(BaseModel):
    train_number: str
    source: str
    destination: str
    fares: List[ClassFare]


# ==========================================
# 8.9 Reservation Rules Interface DTO
# ==========================================
class ReservationRulesResponse(BaseModel):
    quota_rules: Dict[str, str]
    refund_rules: Dict[str, str]
    tatkal_rules: Dict[str, str]


# ==========================================
# 8.10 Railway Circulars Interface DTO
# ==========================================
class CircularDocument(BaseModel):
    circular_id: str
    title: str
    publish_date: str
    url: str
    category: str


class RailwayCircularsResponse(BaseModel):
    circulars: List[CircularDocument]


# ==========================================
# 8.11 Notifications Interface DTO
# ==========================================
class NotificationStatusResponse(BaseModel):
    message_id: str
    status: str
    carrier_ref: Optional[str] = None
    cost: float


# ==========================================
# 8.12 Future Booking Interface DTO
# ==========================================
class BookingResponse(BaseModel):
    booking_id: str
    pnr: Optional[str] = None
    transaction_status: str
    total_amount: float
    booking_reference: Optional[str] = None
