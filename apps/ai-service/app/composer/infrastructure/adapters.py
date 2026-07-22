"""
Infrastructure Adapters for Milestone 6.6 AI Response Composer Platform.
Gateway adapters implementing IUpstreamIntelligencePort for interacting with Memory, Planner, Prediction,
Knowledge (RAG), and Operations subsystems.
"""

from typing import Dict, Any

from app.composer.domain.repositories import IUpstreamIntelligencePort


class InMemoryUpstreamIntelligenceAdapter(IUpstreamIntelligencePort):
    """In-memory gateway adapter simulating upstream AI subsystem responses."""

    def fetch_memory_context(self, traveler_id: str) -> Dict[str, Any]:
        return {
            "traveler_id": traveler_id,
            "has_consent": True,
            "profile": {"full_name": "Mr. Sharma", "age": 67, "is_senior_citizen": True},
            "preferences": {
                "preferred_class": "1AC",
                "berth_preference": "LOWER",
                "meal_preference": "VEG",
            },
        }

    def fetch_journey_plan(self, origin: str, destination: str) -> Dict[str, Any]:
        return {
            "origin": origin or "NDLS",
            "destination": destination or "PUNE",
            "summary": "Direct Rajdhani Express available with Executive and 1AC options.",
            "train_name": "12626 Rajdhani Express",
            "duration": "14h 30m",
            "fare": 3450,
        }

    def fetch_prediction_odds(self, pnr_or_train: str) -> Dict[str, Any]:
        return {
            "train_name": "12626 Rajdhani Express",
            "confirmation_probability": 0.85,
            "confidence": 0.85,
            "delay_forecast_minutes": 15,
        }

    def fetch_knowledge_rules(self, query: str) -> Dict[str, Any]:
        return {
            "clause": "IRCTC-REFUND-CL-14",
            "title": "Cancellation and Refund Rules 2026",
            "requires_policy_citation": True,
            "full_refund_allowed": False,
        }

    def fetch_operational_status(self, train_number: str) -> Dict[str, Any]:
        return {
            "train_number": train_number or "12626",
            "status": "ON_TIME",
            "delay_minutes": 0,
            "current_station": "NDLS",
        }
