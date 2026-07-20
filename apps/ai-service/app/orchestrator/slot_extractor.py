import re
import logging
from typing import Dict, Optional
from app.orchestrator.types import Slot

logger = logging.getLogger("ai-service.orchestrator.slot_extractor")


class SlotExtractor:
    """
    Identifies and extracts travel parameters (stations, PNRs, train numbers, dates)
    from user prompts.
    """

    def __init__(self):
        # Station codes (3-4 uppercase letters, e.g. NDLS, HWH, SBC)
        self.station_pattern = re.compile(r"\b[A-Z]{3,4}\b")
        # Train numbers (5 digits, e.g., 12002, 12626)
        self.train_pattern = re.compile(r"\b\d{5}\b")
        # PNR numbers (10 digits, e.g., 4234567890)
        self.pnr_pattern = re.compile(r"\b\d{10}\b")
        # Date patterns (YYYY-MM-DD)
        self.date_pattern = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
        
        # Mappings of common station names to codes
        self.station_mappings = {
            "delhi": "NDLS",
            "mumbai": "BCT",
            "kolkata": "HWH",
            "chennai": "MAS",
            "bangalore": "SBC",
            "pune": "PUNE",
        }

    def extract_slots(self, text: str, original_text: Optional[str] = None) -> Dict[str, Slot]:
        """
        Parses slots from text. Supports extracting from the raw original text
        to capture PNRs or CCs before masking, if required.
        """
        slots: Dict[str, Slot] = {}
        search_text = original_text or text
        
        # 1. Extract PNR (extract from original before PII redaction)
        pnr_match = self.pnr_pattern.search(search_text)
        if pnr_match:
            val = pnr_match.group(0)
            slots["pnr"] = Slot(name="pnr", value=val, type="PNR", confidence=1.0)
            
        # 2. Extract Train Number
        train_match = self.train_pattern.search(search_text)
        if train_match:
            val = train_match.group(0)
            slots["train_number"] = Slot(name="train_number", value=val, type="TrainNumber", confidence=1.0)

        # 3. Extract Date
        date_match = self.date_pattern.search(search_text)
        if date_match:
            val = date_match.group(0)
            slots["date"] = Slot(name="date", value=val, type="Date", confidence=1.0)
        else:
            # Handle relative dates in lower text
            lower_text = search_text.lower()
            if "today" in lower_text:
                slots["date"] = Slot(name="date", value="today", type="RelativeDate", confidence=0.9)
            elif "tomorrow" in lower_text:
                slots["date"] = Slot(name="date", value="tomorrow", type="RelativeDate", confidence=0.9)

        # 4. Extract Station Codes
        stations = self.station_pattern.findall(search_text)
        station_slots = []
        for station in stations:
            # Avoid picking up PNR or train numbers as station codes
            if station not in station_slots and not station.isdigit():
                station_slots.append(station)
            
        # Also map station names in lowercase
        lower_text = search_text.lower()
        for name, code in self.station_mappings.items():
            if name in lower_text and code not in station_slots:
                station_slots.append(code)

        if len(station_slots) >= 1:
            slots["origin"] = Slot(name="origin", value=station_slots[0], type="StationCode", confidence=0.95)
        if len(station_slots) >= 2:
            slots["destination"] = Slot(name="destination", value=station_slots[1], type="StationCode", confidence=0.95)

        # Extract passenger count heuristics (support optional s for plurals)
        passenger_match = re.search(r"\b(\d+)\s*(?:passenger|adult|people|traveler|seat)s?\b", lower_text)
        if passenger_match:
            val = int(passenger_match.group(1))
            slots["passenger_count"] = Slot(name="passenger_count", value=val, type="PassengerCount", confidence=0.9)

        return slots


slot_extractor = SlotExtractor()
