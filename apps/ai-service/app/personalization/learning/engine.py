# app/personalization/learning/engine.py
from datetime import datetime
import logging
import uuid
from typing import List, Dict
from app.personalization.interfaces.contracts import ILearningEngine
from app.personalization.dto.models import (
    LearningObservationDTO,
    TravelerBehaviorDTO,
    LearningDecisionDTO,
)

logger = logging.getLogger(__name__)


class LearningEngine(ILearningEngine):
    def evaluate(
        self,
        observations: List[LearningObservationDTO],
        behavior: TravelerBehaviorDTO,
    ) -> List[LearningDecisionDTO]:
        logger.info(
            "Evaluating %d observations for learning decisions", len(observations)
        )
        decisions = []

        # Group observations by (action_type, value)
        groups: Dict[tuple, List[LearningObservationDTO]] = {}
        for obs in observations:
            key = (obs.action_type, str(obs.value))
            groups.setdefault(key, []).append(obs)

        # Apply promotion rules
        for (action_type, val_str), obs_list in groups.items():
            if len(obs_list) >= 5:
                if action_type == "SEARCH":
                    if val_str in ("1A", "2A", "3A", "SL", "CC", "2S"):
                        pref_key = "preferred_class"
                        category = "COMFORT"
                        rule = "FrequentSearchClassRule"
                    elif val_str in (
                        "lower",
                        "middle",
                        "upper",
                        "side_lower",
                        "side_upper",
                    ):
                        pref_key = "seat_preference"
                        category = "COMFORT"
                        rule = "FrequentSearchSeatRule"
                    else:
                        continue

                    confidence = min(0.5 + 0.05 * len(obs_list), 0.95)

                    decision = LearningDecisionDTO(
                        decision_id=f"dec-{uuid.uuid4().hex[:12]}",
                        traveler_id=behavior.traveler_profile_id,
                        learning_rule_id=rule,
                        evidence_ids=[obs.observation_id for obs in obs_list],
                        mutation_category=category,
                        mutation_key=pref_key,
                        mutation_value=val_str,
                        confidence_score=confidence,
                        timestamp=datetime.utcnow(),
                    )
                    decisions.append(decision)
                    logger.info(
                        "Learned decision: key=%s value=%s confidence=%f",
                        pref_key,
                        val_str,
                        confidence,
                    )

        return decisions
