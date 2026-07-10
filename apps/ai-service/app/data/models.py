from pydantic import BaseModel, Field
from typing import List, Dict, Any

class DataQualityMetadata(BaseModel):
    provider: str = Field(..., description="Source provider name, e.g. synthetic, irctc, cache")
    last_updated: float = Field(..., description="Timestamp of when this data was fetched")
    data_age_secs: int = Field(default=0, description="Age of the data in seconds")
    confidence: float = Field(default=1.0, description="Data reliability index (0.0 to 1.0)")
    source_type: str = Field(..., description="live, cached, or fallback_synthetic")

class NormalizedTrain(BaseModel):
    train_number: str
    train_name: str
    source: str
    destination: str
    departure: str
    arrival: str
    duration: str
    runs_on: List[str]
    classes: List[str]
    base_fare: Dict[str, int]
    data_quality: DataQualityMetadata

class NormalizedStation(BaseModel):
    code: str
    name: str
    data_quality: DataQualityMetadata

class NormalizedSeatAvailability(BaseModel):
    train_number: str
    booking_class: str
    waitlist_status: str
    fare: int
    data_quality: DataQualityMetadata

class NormalizedPnrStatus(BaseModel):
    pnr: str
    train_number: str
    train_name: str
    journey_date: str
    booking_class: str
    chart_status: str
    passengers: List[Dict[str, Any]]
    data_quality: DataQualityMetadata

class NormalizedDelayHistory(BaseModel):
    train_number: str
    avg_delay_mins: int
    punctuality_rating: str
    cancellation_rate_percent: float
    data_quality: DataQualityMetadata
