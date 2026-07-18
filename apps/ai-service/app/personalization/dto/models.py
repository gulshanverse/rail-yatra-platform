# app/personalization/dto/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime


class TravelerPreferenceDTO(BaseModel):
    preference_id: str
    traveler_profile_id: str
    category: str  # COMFORT, TIMING, MEDICAL, ACCESSIBILITY, etc.
    preference_key: str  # e.g., preferred_class, walking_tolerance
    value: Any
    type: str  # EXPLICIT, IMPLICIT
    version: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TravelerBehaviorDTO(BaseModel):
    behavior_id: str
    traveler_profile_id: str
    active_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    habits: List[Dict[str, Any]] = Field(default_factory=list)
    routines: List[Dict[str, Any]] = Field(default_factory=list)
    last_aggregation_date: datetime


class LearningObservationDTO(BaseModel):
    observation_id: str
    traveler_id: str
    action_type: str  # SEARCH, BOOKING, JOURNEY, GUIDANCE, RECOVERY, NOTIFICATION
    value: Any
    timestamp: datetime
    ttl_expiry: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LearningDecisionDTO(BaseModel):
    decision_id: str
    traveler_id: str
    learning_rule_id: str
    evidence_ids: List[str] = Field(default_factory=list)
    mutation_category: str
    mutation_key: str
    mutation_value: Any
    confidence_score: float
    timestamp: datetime


class PreferenceConfidenceDTO(BaseModel):
    preference_id: str
    score: float  # Normalized between 0.00 and 1.00
    level: str  # HIGH, MEDIUM, LOW
    last_evaluated: datetime
    decay_factor: float


class PreferenceEvidenceDTO(BaseModel):
    evidence_id: str
    preference_id: str
    observation_ids: List[str] = Field(default_factory=list)
    rule_triggers: List[str] = Field(default_factory=list)
    timestamp: datetime


class ReasonCodeDTO(BaseModel):
    code: str  # e.g., PREF_EXPLICIT_CLASS
    category: str
    description: str
    priority: int
    explanation_template: str


class RecommendationAdaptationDTO(BaseModel):
    adaptation_id: str
    target_id: str
    adapted_fields: Dict[str, Any] = Field(default_factory=dict)
    reason_code: str
    timestamp: datetime


class PersonalizedJourneyDTO(BaseModel):
    journey_id: str
    traveler_id: str
    adapted_routes: List[Dict[str, Any]] = Field(default_factory=list)
    applied_preferences: List[str] = Field(default_factory=list)
    explanations: List[Dict[str, Any]] = Field(default_factory=list)
    audit_token: str


class PersonalizedBookingDTO(BaseModel):
    booking_option_id: str
    traveler_id: str
    adapted_seats: List[Dict[str, Any]] = Field(default_factory=list)
    applied_preferences: List[str] = Field(default_factory=list)
    explanations: List[Dict[str, Any]] = Field(default_factory=list)
    audit_token: str


class PersonalizedGuidanceDTO(BaseModel):
    guidance_session_id: str
    traveler_id: str
    adapted_steps: List[Dict[str, Any]] = Field(default_factory=list)
    applied_preferences: List[str] = Field(default_factory=list)
    explanations: List[Dict[str, Any]] = Field(default_factory=list)
    audit_token: str


class PersonalizedRecoveryDTO(BaseModel):
    disruption_id: str
    traveler_id: str
    adapted_options: List[Dict[str, Any]] = Field(default_factory=list)
    applied_preferences: List[str] = Field(default_factory=list)
    explanations: List[Dict[str, Any]] = Field(default_factory=list)
    audit_token: str


class PreferenceAuditDTO(BaseModel):
    audit_id: str
    correlation_id: str
    timestamp: datetime
    traveler_id: str
    action: str  # e.g., PREFERENCE_APPLIED, PREFERENCE_MUTATED
    change_log: Dict[str, Any] = Field(default_factory=dict)
    policy_applied: str
    cryptographic_hash: str


class PreferenceMetricsDTO(BaseModel):
    metric_name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = Field(default_factory=dict)


class TravelerPersonalizationContext(BaseModel):
    traveler_id: str
    version: int
    correlation_id: str
    timestamp: datetime
    persona: str  # WEEKLY_COMMUTER, BUSINESS_TRAVELER, etc.
    explicit_preferences: Dict[str, Any] = Field(default_factory=dict)
    implicit_preferences: Dict[str, Any] = Field(default_factory=dict)
    active_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    active_intent: Dict[str, Any] = Field(default_factory=dict)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    evidence_references: Dict[str, List[str]] = Field(default_factory=dict)
    explanation_context: Dict[str, str] = Field(default_factory=dict)
    audit_signature: str
    telemetry: Dict[str, Any] = Field(default_factory=dict)


class AIReadyPersonalizationContext(BaseModel):
    personalization_context_id: str
    context: TravelerPersonalizationContext
    explanations: List[Dict[str, Any]] = Field(default_factory=list)
    audit_token: str
    timestamp: datetime
