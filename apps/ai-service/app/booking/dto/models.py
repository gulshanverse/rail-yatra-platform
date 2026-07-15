# app/booking/dto/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class BookingRequestDTO(BaseModel):
    traveler_id: str = Field(..., description="Unique traveler profile identifier")
    journey_id: str = Field(..., description="Unique physical route journey identifier")
    preferences: Dict[str, Any] = Field(
        default_factory=dict, description="Passenger seat and comfort preferences"
    )
    timestamp: float = Field(default_factory=datetime.utcnow().timestamp)


class BookingCandidateDTO(BaseModel):
    candidate_id: str
    journey_id: str
    segments: List[Dict[str, Any]]
    selected_quota: str
    boarding_point: str
    class_code: str
    estimated_fare: float


class AvailabilityDTO(BaseModel):
    status: str  # AVAILABLE, RAC, WL
    available_seats: int
    waitlist_position: int
    freshness_timestamp: float


class ConfirmationDTO(BaseModel):
    waitlist_position: int
    days_to_departure: int
    progression_probability: float
    confidence_level: str  # LOW, MEDIUM, HIGH


class QuotaDTO(BaseModel):
    quota_code: str
    eligible_quotas: List[str]
    is_eligible: bool


class BoardingDTO(BaseModel):
    boarding_station: str
    original_boarding_station: str
    boarding_point_changed: bool
    distance_offset_km: float
    no_show_risk: str  # LOW, MEDIUM, HIGH


class RiskDTO(BaseModel):
    overall_risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    risk_factors: List[str]
    connection_failure_probability: float


class ScoreDTO(BaseModel):
    overall_score: float
    confirmation_subscore: float
    cost_subscore: float
    comfort_subscore: float
    duration_subscore: float
    accessibility_subscore: float


class StrategyDTO(BaseModel):
    strategy_key: str
    priority_level: int


class RecommendedBookingDTO(BaseModel):
    candidate_id: str
    candidate: BookingCandidateDTO
    score: ScoreDTO
    risk: RiskDTO
    explanation: Dict[str, Any]
    strategy_tag: str


class BookingRecommendationDTO(BaseModel):
    recommendation_id: str
    correlation_id: str
    primary_candidate: Optional[RecommendedBookingDTO] = None
    alternative_candidates: List[RecommendedBookingDTO] = []
    generated_at: float
    decision_version: str
    ttl_seconds: int


class ExplanationDTO(BaseModel):
    reason_codes: List[str]
    natural_language_explanation: str
    score_breakdown: Dict[str, float]
    risk_breakdown: Dict[str, float]
    evaluated_rules: List[str]
    ai_prompt_context: str


class AuditDTO(BaseModel):
    booking_decision_id: str
    recommendation_id: str
    correlation_id: str
    timestamp: float
    rule_version: str
    strategy_used: str
    score_breakdown: Dict[str, float]
    risk_breakdown: Dict[str, Any]
    confidence: float
    reason_codes: List[str]
    supporting_evidence: Dict[str, Any]
    decision_outcome: str


class MetricsDTO(BaseModel):
    metric_name: str
    value: float
    tags: Dict[str, str]
