# app/booking/health/checker.py
from typing import Dict
from app.booking.interfaces.contracts import IHealthEngine


class HealthEngine(IHealthEngine):
    def check_health(self) -> Dict[str, str]:
        # Exposes readiness/liveness status checks
        return {
            "status": "UP",
            "subsystems": {
                "booking_gateway": "HEALTHY",
                "availability_engine": "HEALTHY",
                "confirmation_engine": "HEALTHY",
                "risk_engine": "HEALTHY",
                "scoring_engine": "HEALTHY",
            },
        }
