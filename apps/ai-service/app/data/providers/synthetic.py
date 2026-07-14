import time
import logging
from typing import List, Optional
from app.data.providers.base import BaseRailwayProvider
from app.data.models import (
    NormalizedTrain,
    NormalizedStation,
    NormalizedSeatAvailability,
    NormalizedPnrStatus,
    NormalizedDelayHistory,
    DataQualityMetadata,
)
from app.tools.train_search import TRAINS_DATABASE
from app.engine.dataset import get_train_delay_metrics
from app.tools.pnr import get_pnr_status as get_pnr_mock

logger = logging.getLogger("ai-service.data.providers.synthetic")


class SyntheticRailwayProvider(BaseRailwayProvider):
    """
    Synthetic provider subclass feeding from sandbox dictionaries and local tools,
    serving as the main fallback/sandbox development source.
    """

    @property
    def name(self) -> str:
        return "synthetic"

    def _get_metadata(self) -> DataQualityMetadata:
        return DataQualityMetadata(
            provider=self.name,
            last_updated=time.time(),
            data_age_secs=0,
            confidence=1.0,
            source_type="fallback_synthetic",
        )

    async def search_trains(
        self, source: str, destination: str
    ) -> List[NormalizedTrain]:
        src = source.strip().upper()
        dest = destination.strip().upper()

        results = []
        for train in TRAINS_DATABASE:
            if train["source"] == src and train["destination"] == dest:
                results.append(
                    NormalizedTrain(
                        train_number=train["train_number"],
                        train_name=train["name"],
                        source=train["source"],
                        destination=train["destination"],
                        departure=train["departure"],
                        arrival=train["arrival"],
                        duration=train["duration"],
                        runs_on=train["runs_on"],
                        classes=train["classes"],
                        base_fare=train["base_fare"],
                        data_quality=self._get_metadata(),
                    )
                )
        return results

    async def get_station_details(
        self, station_code: str
    ) -> Optional[NormalizedStation]:
        code = station_code.strip().upper()
        names = {
            "NDLS": "New Delhi Railway Station",
            "BPL": "Bhopal Junction",
            "MAS": "Chennai Central",
            "HWH": "Howrah Junction",
            "CSMT": "Chhatrapati Shivaji Maharaj Terminus",
            "RKMP": "Rani Kamalapati",
            "NZM": "Hazrat Nizamuddin",
        }
        name = names.get(code, f"{code} Railway Station")
        return NormalizedStation(
            code=code, name=name, data_quality=self._get_metadata()
        )

    async def get_seat_availability(
        self,
        train_number: str,
        source: str,
        destination: str,
        journey_date: str,
        booking_class: str,
    ) -> Optional[NormalizedSeatAvailability]:
        # Synthesize status based on train matching
        status = "Available 24"
        fare = 1200
        for t in TRAINS_DATABASE:
            if t["train_number"] == train_number:
                fare = t["base_fare"].get(booking_class.upper(), 1200)
                if "Rajdhani" in t["name"]:
                    status = "WL 14"
                elif "Kerala" in t["name"]:
                    status = "WL 25"

        return NormalizedSeatAvailability(
            train_number=train_number,
            booking_class=booking_class.upper(),
            waitlist_status=status,
            fare=fare,
            data_quality=self._get_metadata(),
        )

    async def get_pnr_status(self, pnr: str) -> Optional[NormalizedPnrStatus]:
        res = get_pnr_mock(pnr)
        if not res.get("success"):
            return None

        # Parse PNR probability mapping

        return NormalizedPnrStatus(
            pnr=pnr,
            train_number=res["train_number"],
            train_name=res["train_name"],
            journey_date=res["journey_date"],
            booking_class=res["booking_class"],
            chart_status=res["chart_status"],
            passengers=res["passengers"],
            data_quality=self._get_metadata(),
        )

    async def get_delay_history(
        self, train_number: str
    ) -> Optional[NormalizedDelayHistory]:
        metrics = get_train_delay_metrics(train_number)
        return NormalizedDelayHistory(
            train_number=train_number,
            avg_delay_mins=metrics["avg_delay_mins"],
            punctuality_rating=metrics["punctuality_rating"],
            cancellation_rate_percent=metrics["cancellation_rate_percent"],
            data_quality=self._get_metadata(),
        )
