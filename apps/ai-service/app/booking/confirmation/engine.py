# app/booking/confirmation/engine.py
from app.booking.interfaces.contracts import IConfirmationEngine
from app.booking.dto.models import AvailabilityDTO, ConfirmationDTO


class ConfirmationEngine(IConfirmationEngine):
    def evaluate_confirmation(
        self, availability: AvailabilityDTO
    ) -> ConfirmationDTO:
        if availability.status == "AVAILABLE":
            return ConfirmationDTO(
                waitlist_position=0,
                days_to_departure=5,
                progression_probability=1.0,
                confidence_level="HIGH"
            )
            
        wl = availability.waitlist_position
        days = 5  # simulated
        
        # Rule-based progression logic
        if wl <= 10:
            prob = 0.92
            level = "HIGH"
        elif wl <= 30:
            prob = 0.65
            level = "MEDIUM"
        else:
            prob = 0.35
            level = "LOW"
            
        return ConfirmationDTO(
            waitlist_position=wl,
            days_to_departure=days,
            progression_probability=prob,
            confidence_level=level
        )
