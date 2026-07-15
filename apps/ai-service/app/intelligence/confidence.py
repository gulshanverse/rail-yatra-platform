# app/intelligence/confidence.py
import math
from app.intelligence.interfaces import IConfidenceEngine


class ConfidenceEngine(IConfidenceEngine):
    def __init__(self, decay_factor: float = 0.05):
        self.decay_factor = decay_factor

    def calculate_confidence(
        self, provider_id: str, data_freshness_seconds: float, is_official_source: bool
    ) -> float:
        # Determine base confidence rating
        if is_official_source or provider_id.lower() in ("cris", "ntes", "official"):
            base = 100.0
        elif provider_id.lower() in ("confirmtkt", "confirmtkt_gds", "partner"):
            base = 95.0
        elif provider_id.lower() in ("cache", "cache_hit"):
            base = 85.0
        elif provider_id.lower() in ("community", "spotting"):
            base = 50.0
        else:
            base = 30.0

        # Calculate time decay in minutes
        freshness_minutes = max(0.0, data_freshness_seconds / 60.0)
        decay = math.exp(-self.decay_factor * freshness_minutes)

        score = base * decay
        return round(max(0.0, min(100.0, score)), 2)
