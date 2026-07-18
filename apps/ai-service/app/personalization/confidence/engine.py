# app/personalization/confidence/engine.py
from datetime import datetime
import logging
from app.personalization.interfaces.contracts import IConfidenceEngine
from app.personalization.dto.models import PreferenceConfidenceDTO

logger = logging.getLogger(__name__)


class ConfidenceEngine(IConfidenceEngine):
    def calculate(
        self,
        preference_id: str,
        observations: int,
        last_observed: datetime,
    ) -> PreferenceConfidenceDTO:
        initial_confidence_weight = 0.50
        observation_impact_increment = 0.10
        daily_decay_constant = 0.05

        score = initial_confidence_weight + observations * observation_impact_increment
        score = min(max(score, 0.0), 1.0)

        now = datetime.utcnow()
        elapsed_days = (now - last_observed).days
        if elapsed_days > 0:
            score = score * ((1.0 - daily_decay_constant) ** elapsed_days)
            score = min(max(score, 0.0), 1.0)

        if score >= 0.70:
            level = "HIGH"
        elif score >= 0.40:
            level = "MEDIUM"
        else:
            level = "LOW"

        logger.info(
            "Calculated confidence preference_id=%s score=%f level=%s",
            preference_id,
            score,
            level,
        )
        return PreferenceConfidenceDTO(
            preference_id=preference_id,
            score=score,
            level=level,
            last_evaluated=now,
            decay_factor=daily_decay_constant,
        )

    def apply_decay(
        self,
        confidence: PreferenceConfidenceDTO,
    ) -> PreferenceConfidenceDTO:
        now = datetime.utcnow()
        elapsed_days = (now - confidence.last_evaluated).days

        if elapsed_days > 0:
            decay_factor = (
                confidence.decay_factor if confidence.decay_factor is not None else 0.05
            )
            new_score = confidence.score * ((1.0 - decay_factor) ** elapsed_days)
            new_score = min(max(new_score, 0.0), 1.0)
            confidence.score = new_score

            if new_score >= 0.70:
                confidence.level = "HIGH"
            elif new_score >= 0.40:
                confidence.level = "MEDIUM"
            else:
                confidence.level = "LOW"

            confidence.last_evaluated = now
            logger.info(
                "Decayed confidence preference_id=%s to new_score=%f",
                confidence.preference_id,
                new_score,
            )

        return confidence
