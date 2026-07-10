import logging
from typing import Dict, Any, List
from app.engine.models import UserPreferences, TravelOption

logger = logging.getLogger("ai-service.engine.scoring")

class ScoringEngine:
    """
    Extensible, dynamic scoring system that computes cost, comfort, speed,
    and reliability metrics, and applies customized weights based on user preferences.
    """
    def __init__(self):
        # Default baseline weights
        self.default_weights = {
            "cost": 0.25,
            "speed": 0.25,
            "comfort": 0.25,
            "reliability": 0.25
        }

    def compute_sub_scores(self, option: Dict[str, Any], distance_km: int = 500) -> Dict[str, float]:
        """
        Calculates individual sub-scores (0-100) for Cost, Speed, Comfort, and Reliability.
        """
        # 1. Cost Score (lower fare is better)
        # Baseline reference: assume Rs 5 per km is maximum standard fare
        max_ref_fare = distance_km * 5.0
        fare_ratio = min(1.0, option["fare"] / max_ref_fare)
        cost_score = round(100.0 * (1.0 - (fare_ratio * 0.8)), 1)  # offset so even expensive trains don't score 0

        # 2. Speed Score (shorter duration is better)
        # Parse duration (e.g., "8h 40m" -> hours float)
        duration_str = option["duration"]
        hours = 8.0
        try:
            parts = duration_str.split(" ")
            h = float(parts[0].replace("h", ""))
            m = float(parts[1].replace("m", "")) if len(parts) > 1 else 0.0
            hours = h + (m / 60.0)
        except Exception:
            pass
            
        # Baseline reference speed: 45 km/h is slow, 90 km/h is fast
        avg_speed = distance_km / max(1.0, hours)
        speed_score = round(min(100.0, max(10.0, (avg_speed - 40.0) * (90.0 / 50.0))), 1)

        # 3. Comfort Score (dependent on travel class tiers)
        comfort_ratings = {
            "SL": 30.0,
            "CC": 65.0,
            "3A": 75.0,
            "2A": 85.0,
            "1A": 100.0,
            "EC": 95.0
        }
        comfort_score = comfort_ratings.get(option["booking_class"].upper(), 50.0)

        # 4. Reliability Score (higher confirmation probability & lower delays is better)
        conf_prob = option["confirmation_probability"] # 0-100
        delay_mins = option["predicted_delay_mins"]
        
        # Delay penalty (avg delay > 60m is severe penalty)
        delay_penalty = min(50.0, (delay_mins / 60.0) * 25.0)
        reliability_score = round(max(0.0, (conf_prob * 0.7) + (30.0 - delay_penalty)), 1)

        return {
            "cost": cost_score,
            "speed": speed_score,
            "comfort": comfort_score,
            "reliability": reliability_score
        }

    def determine_reason_codes(self, sub_scores: Dict[str, float], option: Dict[str, Any]) -> List[str]:
        """
        Determines reason codes metadata based on high scoring modules and metrics.
        """
        codes = []
        if sub_scores["cost"] >= 80:
            codes.append("LOW_COST")
        if sub_scores["speed"] >= 80:
            codes.append("FAST_TRANSIT")
        if sub_scores["comfort"] >= 85:
            codes.append("HIGH_COMFORT")
        if sub_scores["reliability"] >= 85:
            codes.append("HIGH_RELIABILITY")
        
        # PNR Specific checks
        if option["confirmation_probability"] >= 85 and "WL" in option["waitlist_status"]:
            codes.append("LOW_WAITLIST")
        if option["predicted_delay_mins"] <= 15:
            codes.append("LOW_DELAY")
            
        return codes

    def calculate_overall_score(self, sub_scores: Dict[str, float], preferences: UserPreferences) -> int:
        """
        Merges sub-scores using preference multiplier weights and computes overall score.
        """
        # Apply preference multipliers to weights
        weights = {
            "cost": self.default_weights["cost"] * preferences.budget,
            "speed": self.default_weights["speed"] * preferences.speed,
            "comfort": self.default_weights["comfort"] * preferences.comfort,
            "reliability": self.default_weights["reliability"] * preferences.reliability
        }
        
        # Normalize weights so they sum to 1.0
        total_w = sum(weights.values())
        if total_w > 0:
            weights = {k: v / total_w for k, v in weights.items()}
        else:
            weights = self.default_weights

        # Compute dot product
        overall = sum(sub_scores[k] * weights[k] for k in weights)
        return int(min(100, max(0, round(overall))))

scoring_engine = ScoringEngine()
