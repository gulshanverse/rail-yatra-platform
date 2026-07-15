# app/intelligence/lang.py
from typing import Dict


class LanguageManager:
    def __init__(self):
        # Transliteration dictionary for stations
        self.hindi_to_english: Dict[str, str] = {
            "नई दिल्ली": "NEW DELHI",
            "दिल्ली": "DELHI",
            "आगरा": "AGRA",
            "भोपाल": "BHOPAL",
            "हाजीपुर": "HAJIPUR",
            "हावड़ा": "HOWRAH",
            "मुंबई": "MUMBAI",
        }

    def transliterate_to_english(self, text: str) -> str:
        if not text:
            return ""
        cleaned = text.strip()
        return self.hindi_to_english.get(cleaned, cleaned.upper())

    def get_localized_name(self, station_code: str, lang: str = "en") -> str:
        # Dummy localized names dictionary
        station_names = {
            "NDLS": {"en": "New Delhi", "hi": "नई दिल्ली"},
            "DLI": {"en": "Delhi", "hi": "दिल्ली"},
            "AGC": {"en": "Agra Cantt", "hi": "आगरा कैंट"},
            "BPL": {"en": "Bhopal", "hi": "भोपाल"},
            "CSTM": {"en": "Mumbai CSMT", "hi": "मुंबई सीएसएमटी"},
            "HWH": {"en": "Howrah", "hi": "हावड़ा"},
        }

        station = station_code.upper().strip()
        if station in station_names:
            return station_names[station].get(
                lang.lower(), station_names[station]["en"]
            )
        return station_code
