"""
Station & Platform Congestion Forecaster (FR-4, Capability CP-5).
"""

import logging
from app.predictive.interfaces import (
    StationCongestionForecast,
    RiskLevel,
)

logger = logging.getLogger("ai-service.predictive.congestion")


class StationCongestionForecaster:
    """
    Forecasting engine for station crowd density, queue lengths, and platform changes (FR-4).
    """

    # Major junction station complexity indexes
    JUNCTION_STATIONS = {"NDLS", "HWH", "BCT", "MAS", "SBC", "CSMT", "ADI", "CNB"}

    async def forecast_congestion(self, station_code: str, arrival_hour: int = 14) -> StationCongestionForecast:
        st_code = station_code.upper()
        is_junction = st_code in self.JUNCTION_STATIONS

        # Peak hours: 07:00-10:00 and 17:00-21:00
        is_peak = (7 <= arrival_hour <= 10) or (17 <= arrival_hour <= 21)

        if is_junction and is_peak:
            density = RiskLevel.HIGH
            queue_est = 45
            platform_risk = 35.0
            platform_alloc = "PF-4"
            rec = "Arrive 45 mins early. High crowd density expected on main foot overbridge."
        elif is_junction or is_peak:
            density = RiskLevel.MEDIUM
            queue_est = 20
            platform_risk = 18.0
            platform_alloc = "PF-2"
            rec = "Moderate crowd movement. Allow 25 mins for platform transfer."
        else:
            density = RiskLevel.LOW
            queue_est = 8
            platform_risk = 5.0
            platform_alloc = "PF-1"
            rec = "Normal station flow. Standard 15 min buffer recommended."

        logger.info(f"Station congestion forecast for {st_code} at hour {arrival_hour}: {density.value}")

        return StationCongestionForecast(
            station_code=st_code,
            crowd_density_level=density,
            queue_length_est=queue_est,
            platform_allocation=platform_alloc,
            platform_change_risk=platform_risk,
            recommendation=rec,
        )
