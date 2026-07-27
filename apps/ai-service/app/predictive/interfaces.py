"""
Data structures, enums, and models for the Predictive Intelligence Platform.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PredictionType(str, Enum):
    WAITLIST_PROBABILITY = "WAITLIST_PROBABILITY"
    ARRIVAL_DELAY = "ARRIVAL_DELAY"
    SEAT_AVAILABILITY = "SEAT_AVAILABILITY"
    STATION_CONGESTION = "STATION_CONGESTION"
    MULTI_SEGMENT_RISK = "MULTI_SEGMENT_RISK"
    ALTERNATIVE_JOURNEY = "ALTERNATIVE_JOURNEY"
    PROACTIVE_ALERT = "PROACTIVE_ALERT"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ConsentStatus(str, Enum):
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    ANONYMIZED = "ANONYMIZED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PassengerProfileContext(BaseModel):
    traveler_id: str
    risk_tolerance: RiskLevel = RiskLevel.MEDIUM
    preferred_class: str = "3A"
    consent_status: ConsentStatus = ConsentStatus.GRANTED
    historical_trip_count: int = 0
    pii_redacted: bool = True


class JourneyContext(BaseModel):
    train_number: str
    origin_station: str
    destination_station: str
    travel_date: str
    booking_class: str = "3A"
    quota: str = "GN"
    waitlist_position: Optional[int] = None
    connecting_train_number: Optional[str] = None
    transfer_station: Optional[str] = None
    transfer_buffer_mins: Optional[int] = None
    weather_condition: str = "clear"


class WaitlistPrediction(BaseModel):
    train_number: str
    booking_class: str
    waitlist_position: int
    confirmation_probability: float = Field(..., ge=0.0, le=100.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    clearing_trend: str
    estimated_clearance_days: float
    historical_data_density: int


class DelayPrediction(BaseModel):
    train_number: str
    station_code: str
    predicted_delay_mins: int
    delay_severity: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    weather_impact_mins: int
    historical_on_time_percent: float


class SeatAvailabilityProjection(BaseModel):
    train_number: str
    booking_class: str
    available_seats: int
    projected_exhaustion_hours: float
    quota_conversion_rate: float
    availability_trend: str


class StationCongestionForecast(BaseModel):
    station_code: str
    crowd_density_level: RiskLevel
    queue_length_est: int
    platform_allocation: str
    platform_change_risk: float = Field(..., ge=0.0, le=100.0)
    recommendation: str


class RiskEvaluation(BaseModel):
    journey_id: str
    train_number: str
    connecting_train_number: Optional[str] = None
    missed_connection_probability: float = Field(..., ge=0.0, le=100.0)
    risk_level: RiskLevel
    vulnerability_factors: List[str] = Field(default_factory=list)
    safety_margin_mins: int


class AlternativeOption(BaseModel):
    train_number: str
    train_name: str
    departure_time: str
    arrival_time: str
    booking_class: str
    confirmation_probability: float
    predicted_delay_mins: int
    duration_mins: int
    risk_score: float
    match_score: float


class AlternativeJourneyRecommendation(BaseModel):
    original_train: str
    recommended_alternatives: List[AlternativeOption] = Field(default_factory=list)
    optimization_reason: str
    traveler_match_score: float


class ProactiveAlert(BaseModel):
    alert_id: str
    traveler_id: str
    alert_type: str
    severity: RiskLevel
    message: str
    actionable_recommendation: Optional[str] = None
    dispatched_at: str


class CalibratedPredictionOutput(BaseModel):
    prediction_id: str
    prediction_type: PredictionType
    primary_value: Any
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    explanation_text: str
    evidence_trail: List[str] = Field(default_factory=list)
    consent_verified: bool
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LearningOutcomeSignal(BaseModel):
    prediction_id: str
    train_number: str
    actual_delay_mins: Optional[int] = None
    actual_confirmation_status: Optional[str] = None
    actual_connection_successful: Optional[bool] = None
    error_margin: float = 0.0
    timestamp: str
