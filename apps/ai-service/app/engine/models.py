from pydantic import BaseModel, Field
from typing import List, Optional

class UserPreferences(BaseModel):
    comfort: float = Field(default=1.0, description="Multiplier for comfort preference (1A/2A/CC classes)")
    budget: float = Field(default=1.0, description="Multiplier for cost preference (SL classes, lower pricing)")
    speed: float = Field(default=1.0, description="Multiplier for speed preference (train duration)")
    reliability: float = Field(default=1.0, description="Multiplier for punctuality & waitlist clearing certainty")

class TravelRequirement(BaseModel):
    source: str = Field(..., description="Starting station code (e.g., NDLS)")
    destination: str = Field(..., description="Ending station code (e.g., BPL)")
    journey_date: str = Field(..., description="Target travel date in YYYY-MM-DD format")
    preferred_class: str = Field(default="3A", description="Preferred booking class (SL, 3A, 2A, 1A, CC)")
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    current_wl_position: Optional[int] = Field(default=None, description="Active ticket waitlist position if checking current booking status")

class TravelOption(BaseModel):
    # Train Info
    train_number: str
    train_name: str
    source: str
    destination: str
    departure: str
    arrival: str
    duration: str
    booking_class: str
    fare: int
    waitlist_status: str
    journey_date: str
    
    # Deterministic intelligence metrics
    predicted_delay_mins: int
    confirmation_probability: float  # 0 to 100 percentage
    
    # Architectural requirements
    overall_score: int = Field(..., description="Journey quality score (0 to 100) combining speed, comfort, cost, reliability")
    confidence_score: float = Field(..., description="Prediction certainty score (0.0 to 1.0) decoupled from overall quality")
    reason_codes: List[str] = Field(default_factory=list, description="Reason tags like LOW_WAITLIST, HIGH_COMFORT, etc.")
    
    # Explanations
    advantages: List[str] = Field(default_factory=list)
    disadvantages: List[str] = Field(default_factory=list)
    reasoning: str = ""
    
    # Alternates flags
    is_alternative_station: bool = False
    is_alternative_date: bool = False
    original_boarding_station: Optional[str] = None
    original_journey_date: Optional[str] = None

class RankedRecommendation(BaseModel):
    requirement: TravelRequirement
    options: List[TravelOption]
    best_option_index: int = 0
    tradeoffs_summary: str = Field(..., description="Markdown compiled tradeoffs and options comparisons report")
