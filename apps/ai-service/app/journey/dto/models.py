# app/journey/dto/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class JourneyQueryDTO(BaseModel):
    origin: str = Field(..., min_length=3, max_length=5, description="Origin station code")
    destination: str = Field(..., min_length=3, max_length=5, description="Destination station code")
    earliest_departure: datetime = Field(..., description="Start of departure window")
    latest_arrival: datetime = Field(..., description="End of arrival window")
    traveler_profile: Dict[str, Any] = Field(default_factory=dict, description="Passenger attributes (mobility, age, medical)")
    preference_weights: Dict[str, float] = Field(default_factory=dict, description="Custom subscore preference weights")


class SegmentDTO(BaseModel):
    segment_id: str
    train_number: str
    boarding_station: str
    alighting_station: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    scheduled_boarding_platform: str
    scheduled_alighting_platform: str


class TransferDTO(BaseModel):
    transfer_station: str
    inbound_segment_id: str
    outbound_segment_id: str
    buffer_minutes: int
    walking_distance_meters: int
    platform_change_required: bool


class JourneyCandidateDTO(BaseModel):
    journey_id: str
    segments: List[SegmentDTO]
    transfers: List[TransferDTO]
    total_distance_km: int
    scheduled_duration_minutes: int


class JourneyScoreDTO(BaseModel):
    overall_score: float
    reliability_subscore: float
    comfort_subscore: float
    cost_subscore: float
    duration_subscore: float
    accessibility_subscore: float
    safety_subscore: float
    transfer_subscore: float
    delay_subscore: float
    confidence_subscore: float


class JourneyRiskDTO(BaseModel):
    overall_risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    missed_connection_probability: float
    delay_risk_score: float
    weather_risk_score: float
    safety_risk_score: float
    risk_factors: List[str]


class JourneyExplanationDTO(BaseModel):
    reason_codes: List[str]
    natural_language_explanation: str
    score_breakdown: Dict[str, float]
    risk_breakdown: Dict[str, float]
    evaluated_rules: List[str]
    ai_prompt_context: str


class RecommendedJourneyDTO(BaseModel):
    journey_id: str
    candidate: JourneyCandidateDTO
    score: JourneyScoreDTO
    risk: JourneyRiskDTO
    explanation: JourneyExplanationDTO
    strategy_tag: str
    confidence_score: float


class JourneyRecommendationDTO(BaseModel):
    recommendation_id: str
    primary_candidate: Optional[RecommendedJourneyDTO] = None
    alternative_candidates: List[RecommendedJourneyDTO] = []
    generated_at: float
    decision_version: str
    correlation_id: str
