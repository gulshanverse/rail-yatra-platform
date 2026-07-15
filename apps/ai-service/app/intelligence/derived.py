# app/intelligence/derived.py
from app.intelligence.interfaces import IDerivedIntelligenceEngine


class DerivedIntelligenceEngine(IDerivedIntelligenceEngine):
    def calculate_journey_risk(
        self,
        delay_minutes: int,
        connection_buffer_minutes: int,
        historical_delay_minutes: int,
    ) -> str:
        # 1. Delay exceeds the buffer window entirely
        if delay_minutes >= connection_buffer_minutes:
            return "HIGH"

        # 2. Connection window is extremely tight (< 15 mins buffer left)
        effective_buffer = connection_buffer_minutes - delay_minutes
        if effective_buffer <= 15:
            return "HIGH"

        # 3. Moderate buffer (15-30 mins) or historical delays present threat
        if effective_buffer < 30 or historical_delay_minutes > (effective_buffer - 10):
            return "MEDIUM"

        return "LOW"

    def calculate_platform_stability(
        self, station_code: str, train_number: str
    ) -> float:
        # Simulates a platform stability rating.
        # Trains with numbers ending in '00' or '02' (typically premium Shatabdi/Rajdhani) have higher stability.
        if train_number.endswith(("00", "02")):
            base_stability = 0.95
        else:
            base_stability = 0.80

        # Adjust based on station density (busy terminals like NDLS, HWH have lower platform stability)
        if station_code.upper() in ("NDLS", "HWH", "CSTM"):
            stability = base_stability - 0.15
        else:
            stability = base_stability

        return round(max(0.0, min(1.0, stability)), 2)
