# app/intelligence/conflict.py
from typing import List, Dict, Any
from app.intelligence.interfaces import IConflictResolutionEngine


class ConflictResolutionEngine(IConflictResolutionEngine):
    def resolve_delay_conflict(self, delay_payloads: List[Dict[str, Any]]) -> int:
        if not delay_payloads:
            return 0

        # 1. Filter and search for official sources first (CRIS/NTES)
        official_sources = [
            p
            for p in delay_payloads
            if p.get("provider_id", "").lower() in ("cris", "ntes", "official")
            or p.get("is_official_source", False)
        ]

        target_list = official_sources if official_sources else delay_payloads

        # 2. Sort by freshness (newest sync_timestamp first)
        target_list.sort(key=lambda x: x.get("sync_timestamp", 0.0), reverse=True)

        # 3. If multiple have the same freshness, sort by confidence_score
        target_list.sort(key=lambda x: x.get("confidence_score", 0.0), reverse=True)

        return int(target_list[0].get("delay_minutes", 0))

    def resolve_platform_conflict(self, platform_payloads: List[Dict[str, Any]]) -> str:
        if not platform_payloads:
            return ""

        # Prefer official station master inputs
        official_sources = [
            p
            for p in platform_payloads
            if p.get("provider_id", "").lower()
            in ("ntes", "official", "station_master")
            or p.get("is_official_source", False)
        ]

        target_list = official_sources if official_sources else platform_payloads

        # Sort by freshness (newest first)
        target_list.sort(key=lambda x: x.get("sync_timestamp", 0.0), reverse=True)

        # Sort by confidence_score
        target_list.sort(key=lambda x: x.get("confidence_score", 0.0), reverse=True)

        return str(target_list[0].get("platform_number", ""))
