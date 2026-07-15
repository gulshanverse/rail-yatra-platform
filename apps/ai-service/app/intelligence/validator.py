# app/intelligence/validator.py
import re
from datetime import datetime, date
from app.intelligence.interfaces import IDomainValidator


class DomainValidator(IDomainValidator):
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self._train_pattern = re.compile(r"^\d{5}$")
        self._station_pattern = re.compile(r"^[A-Z]{3,5}$")
        self._pnr_pattern = re.compile(r"^\d{10}$")
        self._coach_pattern = re.compile(r"^[A-Z0-9]{2,4}$")
        self._platform_pattern = re.compile(r"^[a-zA-Z0-9-]{1,5}$")

    def validate_train_number(self, train_number: str) -> bool:
        if not train_number:
            return False
        return bool(self._train_pattern.match(train_number.strip()))

    def validate_station_code(self, station_code: str) -> bool:
        if not station_code:
            return False
        return bool(self._station_pattern.match(station_code.strip().upper()))

    def validate_pnr(self, pnr: str) -> bool:
        if not pnr:
            return False
        cleaned = pnr.strip()
        if not self._pnr_pattern.match(cleaned):
            return False
        # First digit check (1-8, excluding 0, 9 for Indian Railways PNRs)
        first_digit = int(cleaned[0])
        return 1 <= first_digit <= 8

    def validate_coach_label(self, coach_label: str) -> bool:
        if not coach_label:
            return False
        return bool(self._coach_pattern.match(coach_label.strip().upper()))

    def validate_platform_number(self, platform_number: str) -> bool:
        if not platform_number:
            return False
        return bool(self._platform_pattern.match(platform_number.strip()))

    def validate_date(self, date_str: str) -> bool:
        if not date_str:
            return False
        try:
            # Parse date in format YYYY-MM-DD
            target_date = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
            today = date.today()
            # Advanced Reservation Period (ARP) is 120 days
            delta = (target_date - today).days
            return 0 <= delta <= 120
        except ValueError:
            return False
