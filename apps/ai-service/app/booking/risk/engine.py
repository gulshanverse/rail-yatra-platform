# app/booking/risk/engine.py
from app.booking.interfaces.contracts import IRiskEngine
from app.booking.dto.models import BookingCandidateDTO, AvailabilityDTO, ConfirmationDTO, BoardingDTO, RiskDTO


class RiskEngine(IRiskEngine):
    def calculate_risk(
        self,
        candidate: BookingCandidateDTO,
        availability: AvailabilityDTO,
        confirmation: ConfirmationDTO,
        boarding: BoardingDTO
    ) -> RiskDTO:
        factors = []
        connection_fail = 0.02
        
        # 1. Evaluate waitlist status risks
        if availability.status == "WL":
            prob = 1.0 - confirmation.progression_probability
            connection_fail += prob
            if prob > 0.40:
                factors.append("HIGH_WAITLIST_CANCELLATION_RISK")
            else:
                factors.append("WAITLIST_CONGESTION")
                
        # 2. Boarding change risks
        if boarding.boarding_point_changed:
            connection_fail += 0.15
            factors.append("BOARDING_POINT_CHANGE_NO_SHOW")
            
        # 3. Class level stability
        if candidate.class_code == "SL":
            factors.append("SLEEPER_UNCONFIRMED_PASSENGER_RISK")
            
        # Normalize and bound
        connection_fail = min(1.0, max(0.0, connection_fail))
        
        if connection_fail > 0.70:
            level = "CRITICAL"
        elif connection_fail > 0.40:
            level = "HIGH"
        elif connection_fail > 0.15:
            level = "MEDIUM"
        else:
            level = "LOW"
            
        return RiskDTO(
            overall_risk_level=level,
            risk_factors=factors,
            connection_failure_probability=round(connection_fail, 2)
        )
