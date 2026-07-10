import time
import logging
from typing import List, Dict, Any, Optional
from app.data.providers.synthetic import SyntheticRailwayProvider
from app.data.health import provider_health_monitor
from app.data.cache import railway_cache_manager
from app.data.models import (
    NormalizedTrain,
    NormalizedStation,
    NormalizedSeatAvailability,
    NormalizedPnrStatus,
    NormalizedDelayHistory
)

logger = logging.getLogger("ai-service.data.manager")

class RailwayDataManager:
    """
    Central orchestration gateway for the Railway Data Platform.
    Ensures that clients read from cache, select healthy providers, and gracefully
    degrade to synthetic datasets if API exceptions are encountered.
    """
    def __init__(self):
        # In a real app we'd load multiple provider instances. Here we register adapters:
        self.providers = {
            "synthetic": SyntheticRailwayProvider()
        }
        # default failover sequence order
        self.provider_priority = ["synthetic"]

    def _mark_cache_quality(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Modifies data quality descriptor to highlight cached source type."""
        if "data_quality" in data_dict:
            data_dict["data_quality"]["source_type"] = "cached"
            data_dict["data_quality"]["data_age_secs"] = int(time.time() - data_dict["data_quality"].get("last_updated", time.time()))
        return data_dict

    async def search_trains(self, source: str, destination: str) -> List[NormalizedTrain]:
        key = f"{source}_{destination}"
        
        # 1. Try fetching from Cache
        cached = railway_cache_manager.get("schedule", key)
        if cached:
            logger.info(f"Cache Hit: search_trains for {key}")
            return [NormalizedTrain(**self._mark_cache_quality(t)) for t in cached]

        # 2. Iterate through healthy providers
        for prov_name in self.provider_priority:
            if provider_health_monitor.is_healthy(prov_name) or prov_name == "synthetic":
                try:
                    provider = self.providers[prov_name]
                    results = await provider.search_trains(source, destination)
                    
                    # Save to cache
                    serialized_list = [t.model_dump() for t in results]
                    railway_cache_manager.set("schedule", key, serialized_list)
                    
                    provider_health_monitor.record_success(prov_name)
                    return results
                except Exception as e:
                    logger.error(f"Provider '{prov_name}' search_trains failed: {e}")
                    provider_health_monitor.record_failure(prov_name)

        # Fallback empty list
        return []

    async def get_station_details(self, station_code: str) -> Optional[NormalizedStation]:
        key = station_code.strip().upper()
        
        # 1. Try cache
        cached = railway_cache_manager.get("station", key)
        if cached:
            logger.info(f"Cache Hit: get_station_details for {key}")
            return NormalizedStation(**self._mark_cache_quality(cached))

        # 2. Try providers
        for prov_name in self.provider_priority:
            if provider_health_monitor.is_healthy(prov_name) or prov_name == "synthetic":
                try:
                    provider = self.providers[prov_name]
                    res = await provider.get_station_details(station_code)
                    if res:
                        railway_cache_manager.set("station", key, res.model_dump())
                        provider_health_monitor.record_success(prov_name)
                        return res
                except Exception as e:
                    logger.error(f"Provider '{prov_name}' get_station_details failed: {e}")
                    provider_health_monitor.record_failure(prov_name)
        return None

    async def get_seat_availability(
        self,
        train_number: str,
        source: str,
        destination: str,
        journey_date: str,
        booking_class: str
    ) -> Optional[NormalizedSeatAvailability]:
        key = f"{train_number}_{source}_{destination}_{journey_date}_{booking_class}"
        
        # 1. Try cache
        cached = railway_cache_manager.get("availability", key)
        if cached:
            logger.info(f"Cache Hit: get_seat_availability for {key}")
            return NormalizedSeatAvailability(**self._mark_cache_quality(cached))

        # 2. Try providers
        for prov_name in self.provider_priority:
            if provider_health_monitor.is_healthy(prov_name) or prov_name == "synthetic":
                try:
                    provider = self.providers[prov_name]
                    res = await provider.get_seat_availability(
                        train_number, source, destination, journey_date, booking_class
                    )
                    if res:
                        railway_cache_manager.set("availability", key, res.model_dump())
                        provider_health_monitor.record_success(prov_name)
                        return res
                except Exception as e:
                    logger.error(f"Provider '{prov_name}' get_seat_availability failed: {e}")
                    provider_health_monitor.record_failure(prov_name)
        return None

    async def get_pnr_status(self, pnr: str) -> Optional[NormalizedPnrStatus]:
        key = pnr.strip()
        
        # 1. Try cache
        cached = railway_cache_manager.get("pnr", key)
        if cached:
            logger.info(f"Cache Hit: get_pnr_status for {key}")
            return NormalizedPnrStatus(**self._mark_cache_quality(cached))

        # 2. Try providers
        for prov_name in self.provider_priority:
            if provider_health_monitor.is_healthy(prov_name) or prov_name == "synthetic":
                try:
                    provider = self.providers[prov_name]
                    res = await provider.get_pnr_status(pnr)
                    if res:
                        railway_cache_manager.set("pnr", key, res.model_dump())
                        provider_health_monitor.record_success(prov_name)
                        return res
                except Exception as e:
                    logger.error(f"Provider '{prov_name}' get_pnr_status failed: {e}")
                    provider_health_monitor.record_failure(prov_name)
        return None

    async def get_delay_history(self, train_number: str) -> Optional[NormalizedDelayHistory]:
        key = train_number.strip()
        
        # 1. Try cache
        cached = railway_cache_manager.get("delay", key)
        if cached:
            logger.info(f"Cache Hit: get_delay_history for {key}")
            return NormalizedDelayHistory(**self._mark_cache_quality(cached))

        # 2. Try providers
        for prov_name in self.provider_priority:
            if provider_health_monitor.is_healthy(prov_name) or prov_name == "synthetic":
                try:
                    provider = self.providers[prov_name]
                    res = await provider.get_delay_history(train_number)
                    if res:
                        railway_cache_manager.set("delay", key, res.model_dump())
                        provider_health_monitor.record_success(prov_name)
                        return res
                except Exception as e:
                    logger.error(f"Provider '{prov_name}' get_delay_history failed: {e}")
                    provider_health_monitor.record_failure(prov_name)
        return None

railway_data_manager = RailwayDataManager()
