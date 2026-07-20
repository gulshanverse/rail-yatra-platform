import logging
from typing import Dict, Any, List
from app.orchestrator.types import IntentDescriptor, IntentCandidate, Slot
from app.orchestrator.config import platform_config

logger = logging.getLogger("ai-service.orchestrator.evaluator")


class ConfidenceEvaluator:
    """
    Evaluates classification confidence margins, checks required slot parameters,
    and constructs the final IntentDescriptor DTO.
    """

    def __init__(self):
        # Fetch configuration thresholds or fall back to standard defaults
        self.intent_threshold = platform_config.get("intent_confidence_threshold", 0.70)
        self.slot_threshold = platform_config.get("slot_confidence_threshold", 0.65)
        
        # Required slots by intent family
        self.required_slots = {
            "plan_travel": ["origin", "destination"],
            "check_pnr": ["pnr"],
            "journey_intelligence": ["train_number"],
        }

    def evaluate(
        self,
        candidate: IntentCandidate,
        slots: Dict[str, Slot],
        context: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> IntentDescriptor:
        """
        Runs quality validation checks and constructs the IntentDescriptor.
        """
        needs_clarification = False
        errors: List[str] = []

        # 1. Intent confidence check
        if candidate.confidence < self.intent_threshold:
            logger.warning(
                f"Intent '{candidate.name}' confidence {candidate.confidence} falls below threshold {self.intent_threshold}."
            )
            needs_clarification = True
            errors.append("Low intent classification confidence.")

        # 2. Check for missing required slots for the intent
        intent_name = candidate.name.lower()
        if intent_name in self.required_slots:
            for req_slot in self.required_slots[intent_name]:
                if req_slot not in slots:
                    logger.warning(f"Required slot '{req_slot}' missing for intent '{intent_name}'.")
                    needs_clarification = True
                    errors.append(f"Missing required slot: {req_slot}")

        # 3. Check for low-confidence slots
        for name, slot in slots.items():
            if slot.confidence < self.slot_threshold:
                logger.warning(
                    f"Slot '{name}' confidence {slot.confidence} falls below threshold {self.slot_threshold}."
                )
                needs_clarification = True
                errors.append(f"Low slot confidence: {name}")

        # Package validation errors into context/metadata lists
        if errors:
            context["validation_errors"] = errors

        return IntentDescriptor(
            intent=candidate,
            slots=slots,
            context=context,
            metadata=metadata,
            needs_clarification=needs_clarification,
        )


confidence_evaluator = ConfidenceEvaluator()
