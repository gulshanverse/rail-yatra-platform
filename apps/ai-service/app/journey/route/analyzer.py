# app/journey/route/analyzer.py
from typing import Dict, Any
from app.journey.interfaces.contracts import IRouteAnalyzer
from app.journey.dto.models import JourneyCandidateDTO


class RouteAnalyzer(IRouteAnalyzer):
    def __init__(self, intelligence_gateway: Any = None):
        self.intelligence_gateway = intelligence_gateway

    async def analyze_route(
        self, candidate: JourneyCandidateDTO
    ) -> Dict[str, Any]:
        # Evaluates operational stability parameters
        # We compute mock values grounded in realistic rules:
        # Trains ending in "00" or "02" are premium superfast, hence high stability.
        
        has_premium_train = False
        avg_historical_delay = 10.0
        
        for segment in candidate.segments:
            if segment.train_number.endswith(("00", "02")):
                has_premium_train = True
            
            # Simple simulation: non-superfast trains or long distance lines have higher delay trends
            if int(segment.train_number) % 2 == 1:
                avg_historical_delay += 25.0

        stability_score = 0.95 if has_premium_train else 0.80
        congestion_index = 0.40 if len(candidate.segments) > 1 else 0.15
        diversion_risk = 0.02 if not has_premium_train else 0.005

        return {
            "route_stability": stability_score,
            "average_delay_minutes": avg_historical_delay,
            "diversion_risk": diversion_risk,
            "congestion_index": congestion_index,
            "station_complexity": 0.50 if len(candidate.transfers) > 0 else 0.15
        }
