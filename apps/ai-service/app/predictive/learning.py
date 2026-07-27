"""
Continuous Learning Coordinator (CP-8, Learning Domain).
"""

import logging
from typing import Dict, Any
from app.predictive.interfaces import LearningOutcomeSignal

logger = logging.getLogger("ai-service.predictive.learning")


class ContinuousLearningCoordinator:
    """
    Coordinator for capturing post-journey physical outcomes and updating predictive feedback loops (CP-8).
    """

    def __init__(self):
        self._registered_signals: Dict[str, LearningOutcomeSignal] = {}
        self._total_error_accumulator: float = 0.0
        self._signal_count: int = 0

    def register_physical_outcome(self, signal: LearningOutcomeSignal) -> Dict[str, Any]:
        """
        Registers actual journey arrival times or waitlist clearance outcomes.
        Calculates error margins and updates model retraining triggers.
        """
        self._registered_signals[signal.prediction_id] = signal
        self._signal_count += 1
        self._total_error_accumulator += abs(signal.error_margin)

        avg_mae = round(self._total_error_accumulator / max(1, self._signal_count), 2)
        retrain_triggered = avg_mae > 15.0 or self._signal_count % 100 == 0

        logger.info(
            f"Learning Coordinator registered outcome for {signal.prediction_id}: Error margin {signal.error_margin}. MAE: {avg_mae}"
        )

        return {
            "prediction_id": signal.prediction_id,
            "registered": True,
            "current_mae": avg_mae,
            "total_outcomes_logged": self._signal_count,
            "retraining_trigger_activated": retrain_triggered,
        }

    def get_accuracy_metrics(self) -> Dict[str, Any]:
        return {
            "logged_outcomes_count": self._signal_count,
            "mean_absolute_error": round(self._total_error_accumulator / max(1, self._signal_count), 2),
            "model_health_status": "OPTIMAL" if self._signal_count == 0 or (self._total_error_accumulator / self._signal_count) <= 15.0 else "DRIFT_WARNING",
        }
