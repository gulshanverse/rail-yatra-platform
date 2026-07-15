# app/journey/transfer/analyzer.py
from typing import Dict, Any
from app.journey.interfaces.contracts import ITransferAnalyzer
from app.journey.dto.models import JourneyCandidateDTO
from app.journey.config.registry import get_policy


class TransferAnalyzer(ITransferAnalyzer):
    def evaluate_transfers(
        self, candidate: JourneyCandidateDTO, traveler_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Fetch policy limits
        policy = get_policy("Transfer")
        mct_same = policy.get("mct_same_platform", 15)
        mct_cross = policy.get("mct_cross_platform", 30)

        is_senior = traveler_profile.get("is_senior", False)
        walking_speed = policy.get("senior_walking_speed_mps", 0.8) if is_senior else policy.get("base_walking_speed_mps", 1.2)

        total_walk_time_minutes = 0.0
        missed_connection_probability = 0.0

        for transfer in candidate.transfers:
            # Platform walking calculation
            distance = transfer.walking_distance_meters
            walk_seconds = distance / walking_speed
            walk_minutes = walk_seconds / 60.0
            total_walk_time_minutes += walk_minutes

            # Connection validation rules
            required_mct = mct_cross if transfer.platform_change_required else mct_same
            if transfer.buffer_minutes < required_mct:
                # High risk of missing transfer
                missed_connection_probability += 0.60
            elif transfer.buffer_minutes < required_mct + 15:
                # Moderate risk
                missed_connection_probability += 0.25
            else:
                # Safe layover
                missed_connection_probability += 0.02

        # Bound probability to [0.0, 1.0]
        missed_connection_probability = min(1.0, max(0.0, missed_connection_probability))

        return {
            "total_walking_minutes": round(total_walk_time_minutes, 2),
            "missed_connection_probability": missed_connection_probability,
            "requires_escalator": is_senior,
            "transfer_complexity_index": 0.80 if len(candidate.transfers) > 1 else 0.30
        }
