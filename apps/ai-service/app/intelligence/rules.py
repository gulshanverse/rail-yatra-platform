# app/intelligence/rules.py
from datetime import datetime
from app.intelligence.interfaces import IBusinessRuleEngine


class BusinessRuleEngine(IBusinessRuleEngine):
    def __init__(self):
        # Flat cancellation charges per class
        self.flat_charges = {
            "1A": 240.0,
            "2A": 200.0,
            "3A": 180.0,
            "3E": 180.0,
            "CC": 180.0,
            "SL": 120.0,
            "2S": 60.0,
        }

    def evaluate_refund_policy(
        self,
        cancellation_status: str,
        booking_class: str,
        hours_before_departure: int,
        base_fare: float,
    ) -> float:
        # If train is cancelled, full refund is returned automatically
        if cancellation_status.upper() in ("CANCELLED", "FULL_CANCELLED"):
            return base_fare

        # Get flat cancellation charge for this booking class
        flat_charge = self.flat_charges.get(booking_class.upper(), 120.0)

        # 1. More than 48 hours before departure
        if hours_before_departure >= 48:
            refund = base_fare - flat_charge
            return max(0.0, refund)

        # 2. Between 12 hours and 48 hours before departure
        elif 12 <= hours_before_departure < 48:
            # Cancellation charge is 25% of fare or flat charge (whichever is higher)
            charge = max(base_fare * 0.25, flat_charge)
            refund = base_fare - charge
            return max(0.0, refund)

        # 3. Between 4 hours and 12 hours before departure
        elif 4 <= hours_before_departure < 12:
            # Cancellation charge is 50% of fare or flat charge (whichever is higher)
            charge = max(base_fare * 0.50, flat_charge)
            refund = base_fare - charge
            return max(0.0, refund)

        # 4. Less than 4 hours before departure (or post chart preparation)
        else:
            return 0.0

    def is_tatkal_window_active(self, class_type: str, current_time_str: str) -> bool:
        """
        AC class opens at 10:00 AM, Non-AC class opens at 11:00 AM.
        Checks if current time is within the first active hour of the booking window (10-11 or 11-12).
        """
        try:
            parsed_time = datetime.strptime(current_time_str.strip(), "%H:%M").time()
            hour = parsed_time.hour

            is_ac = class_type.upper() in ("1A", "2A", "3A", "3E", "CC")

            if is_ac:
                # AC Tatkal opens at 10:00 AM. Active window: 10:00 to 11:00.
                return hour == 10
            else:
                # Non-AC Tatkal opens at 11:00 AM. Active window: 11:00 to 12:00.
                return hour == 11
        except ValueError:
            return False
