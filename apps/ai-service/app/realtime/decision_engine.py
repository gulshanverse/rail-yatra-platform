"""
Operational Decision Support Engine for Phase 8 Real-Time Operations Platform.
"""

from typing import List
from app.realtime.interfaces import IncidentSeverity
from app.realtime.models import Incident, JourneyState


class DecisionEngine:
    def generate_recommendations(
        self, incident: Incident, journey_state: JourneyState
    ) -> List[str]:
        """Generates operational recommendations based on incident severity and passenger journey state."""
        recommendations: List[str] = []

        if incident.severity == IncidentSeverity.CRITICAL:
            recommendations.append(
                "Immediate re-booking recommended via alternative express service."
            )
            recommendations.append("Full refund policy applicable under cancellation rules.")
        elif incident.severity == IncidentSeverity.HIGH:
            if journey_state.transfer_risk:
                recommendations.append(
                    "High risk of missed connecting train. Evaluate alternate connection at junction."
                )
            recommendations.append(
                f"Proceed to station lounge; estimated delay is {incident.description}."
            )
        elif incident.severity == IncidentSeverity.MEDIUM:
            recommendations.append(
                "Monitor live platform displays. Refresh RailYatra dynamic ETA before boarding."
            )
        else:
            recommendations.append("No immediate action required. Continue planned journey.")

        return recommendations
