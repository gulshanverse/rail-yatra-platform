# app/intelligence/normalizer.py
import re
from typing import Any, Dict
from app.intelligence.interfaces import INormalizationEngine


class NormalizationEngine(INormalizationEngine):
    def __init__(self):
        # Sample alias mapping dictionary
        self.station_aliases: Dict[str, str] = {
            "NEW DELHI": "NDLS",
            "DELHI": "DLI",
            "AGRA CANTT": "AGC",
            "AGRA": "AGC",
            "BHOPAL": "BPL",
            "HAZRAT NIZAMUDDIN": "NZM",
            "NIZAMUDDIN": "NZM",
            "MUMBAI CST": "CSTM",
            "MUMBAI": "CSTM",
            "CST MUMBAI": "CSTM",
            "HOWRAH": "HWH",
            "KOLKATA": "HWH",
            "PATNA": "PNBE",
            "BENGALURU": "SBC",
            "BANGALORE": "SBC",
            "नई दिल्ली": "NDLS",
            "दिल्ली": "DLI",
            "आगरा": "AGC",
            "भोपाल": "BPL",
        }
        self._minutes_pattern = re.compile(
            r"(\d+)\s*(min|minute|mins|minutes)", re.IGNORECASE
        )
        self._hours_pattern = re.compile(r"(\d+)\s*(hour|hr|hours|hrs)", re.IGNORECASE)

    def normalize_station_code(self, raw_station: str) -> str:
        if not raw_station:
            return ""
        cleaned = raw_station.strip().upper()
        # Check alias map
        if cleaned in self.station_aliases:
            return self.station_aliases[cleaned]
        # Return alphabetic match or default uppercase strip
        alphabetic = re.sub(r"[^A-Z]", "", cleaned)
        return alphabetic if len(alphabetic) >= 3 else cleaned

    def normalize_delay(self, raw_delay: Any) -> int:
        if raw_delay is None:
            return 0
        if isinstance(raw_delay, (int, float)):
            return int(raw_delay)

        delay_str = str(raw_delay).strip()
        if not delay_str:
            return 0

        # Parse formats like "15 mins", "1 hour 15 mins", "02:15"
        delay_str_lower = delay_str.lower()

        # Check for HH:MM format
        time_match = re.match(r"^(\d{1,2}):(\d{2})$", delay_str)
        if time_match:
            hours, minutes = map(int, time_match.groups())
            return hours * 60 + minutes

        # Check text patterns
        total_minutes = 0
        hours_match = self._hours_pattern.search(delay_str_lower)
        if hours_match:
            total_minutes += int(hours_match.group(1)) * 60

        mins_match = self._minutes_pattern.search(delay_str_lower)
        if mins_match:
            total_minutes += int(mins_match.group(1))

        if not hours_match and not mins_match:
            # Fallback check if it's just raw numeric characters
            digits = re.sub(r"\D", "", delay_str)
            if digits:
                return int(digits)
            return 0

        return total_minutes

    def normalize_class_code(self, raw_class: str) -> str:
        if not raw_class:
            return ""
        cleaned = raw_class.strip().upper()
        # Normalization maps
        mappings = {
            "FIRST AC": "1A",
            "AC 1": "1A",
            "1AC": "1A",
            "AC FIRST CLASS": "1A",
            "AC 2 TIER": "2A",
            "AC 2": "2A",
            "2AC": "2A",
            "AC 2-TIER": "2A",
            "AC 3 TIER": "3A",
            "AC 3": "3A",
            "3AC": "3A",
            "AC 3-TIER": "3A",
            "AC 3 ECONOMY": "3E",
            "3E": "3E",
            "3AC ECONOMY": "3E",
            "AC CHAIR CAR": "CC",
            "CHAIR CAR": "CC",
            "CC": "CC",
            "SLEEPER CLASS": "SL",
            "SLEEPER": "SL",
            "SL": "SL",
            "SECOND SEATING": "2S",
            "2S": "2S",
            "RESERVED SECOND SEATING": "2S",
            "GENERAL": "GN",
            "UNRESERVED": "GN",
            "GN": "GN",
        }
        return mappings.get(cleaned, cleaned)

    def normalize_platform_number(self, raw_platform: Any) -> str:
        if raw_platform is None:
            return ""
        cleaned = str(raw_platform).strip().upper()
        # Match digits/chars from string like "PF-1" or "PLATFORM 3"
        pf_match = re.search(r"(?:PF|PLATFORM|PF-|PLATFORM-)?\s*([A-Z0-9]+)", cleaned)
        if pf_match:
            return pf_match.group(1)
        return cleaned

    def normalize_quota_code(self, raw_quota: str) -> str:
        if not raw_quota:
            return "GN"
        cleaned = raw_quota.strip().upper()
        mappings = {
            "GENERAL": "GN",
            "GN": "GN",
            "TATKAL": "TQ",
            "TQ": "TQ",
            "CK": "TQ",
            "PREMIUM TATKAL": "PT",
            "PT": "PT",
            "LADIES": "LD",
            "LD": "LD",
            "SENIOR CITIZEN": "SS",
            "LOWER BERTH": "SS",
            "SS": "SS",
        }
        return mappings.get(cleaned, "GN")
