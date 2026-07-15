# app/intelligence/freshness.py
from app.intelligence.interfaces import IFreshnessEngine


class FreshnessEngine(IFreshnessEngine):
    def __init__(self):
        # Configure staleness parameters
        self.max_age_limits = {
            "live_train_status": 60.0,
            "pnr_lookup": 30.0,
            "pnr_status": 30.0,
            "seat_availability": 300.0,
            "train_schedule": 2592000.0,
            "schedule": 2592000.0,
            "station_info": 2592000.0,
            "platform_info": 300.0,
            "coach_position": 86400.0,
            "fare_inquiry": 86400.0,
            "circulars": 604800.0,  # 7 days
        }

    def get_max_age_seconds(self, capability: str) -> float:
        return self.max_age_limits.get(capability.lower(), 300.0)

    def is_stale(self, capability: str, data_age_seconds: float) -> bool:
        limit = self.get_max_age_seconds(capability)
        return data_age_seconds > limit
