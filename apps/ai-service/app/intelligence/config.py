# app/intelligence/config.py
from pydantic_settings import BaseSettings


class IntelligenceSettings(BaseSettings):
    strict_validation: bool = True
    decay_factor: float = 0.05
    arp_days: int = 120
    cache_ttl_seconds: int = 300
    telemetry_enabled: bool = True
    official_priority_weight: float = 1.5

    class Config:
        env_prefix = "INTELLIGENCE_"


intelligence_settings = IntelligenceSettings()
