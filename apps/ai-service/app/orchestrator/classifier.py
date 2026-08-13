import logging
import json
import re
import time
from typing import Dict, Any, Optional

from app.agents.base import extract_text_content, _run_with_failover
from app.prompts.classifier import INTENT_CLASSIFIER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

from app.orchestrator.normalizer import input_normalizer
from app.orchestrator.slot_extractor import slot_extractor
from app.orchestrator.evaluator import confidence_evaluator
from app.orchestrator.types import IntentDescriptor, IntentCandidate

logger = logging.getLogger("ai-service.orchestrator.classifier")


class IntentClassifier:
    """Classify user intent with a local fast path and quota-aware model fallback."""

    def _classify_heuristics(self, text: str) -> Optional[IntentCandidate]:
        msg = text.lower()
        intent = None
        reason = "Heuristic regex match"

        if any(k in msg for k in ["pnr", "ticket status", "booking status"]):
            intent = "check_pnr"
        elif any(
            k in msg
            for k in ["train", "route", "schedule", "go to", "travel to", "from", "to"]
        ):
            intent = "plan_travel"
        elif any(
            k in msg for k in ["waitlist", "delay", "confirm", "forecast", "prediction"]
        ):
            intent = "journey_intelligence"
        elif any(k in msg for k in ["policy", "luggage", "refund", "faq", "rules"]):
            intent = "knowledge"
        elif any(
            k in msg for k in ["recommend", "better", "compare", "score", "comfort", "rate"]
        ):
            intent = "recommendation"

        if intent:
            logger.info("Heuristic classifier matched: %s", intent)
            return IntentCandidate(name=intent, confidence=1.0, reason=reason)
        return None

    async def _classify_model(self, text: str) -> IntentCandidate:
        logger.info("Sending text to quota-aware LLM classifier: '%s'", text)
        messages = [
            SystemMessage(content=INTENT_CLASSIFIER_PROMPT),
            HumanMessage(content=text),
        ]

        try:
            response = await _run_with_failover(messages, complexity="standard")
            content = extract_text_content(response.content).strip()
            clean_content = re.sub(
                r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE
            ).strip()
            data = json.loads(clean_content)
            intent = data.get("intent", "conversation").lower()
            confidence = float(data.get("confidence", 0.5))
            reason = data.get("reason", "Parsed classification output.")
            logger.info("Model classifier returned: %s (confidence: %.2f)", intent, confidence)
            return IntentCandidate(name=intent, confidence=confidence, reason=reason)
        except Exception as e:
            logger.error("LLM classification failed: %s. Falling back to heuristics.", e)
            fallback = self._classify_heuristics(text)
            if fallback:
                return fallback
            return IntentCandidate(
                name="conversation",
                confidence=0.5,
                reason="Fallback due to LLM exception.",
            )

    async def classify_and_parse(
        self, user_message: str, trace_id: str = "default-trace"
    ) -> IntentDescriptor:
        start_time = time.time()
        normalized = input_normalizer.normalize(user_message)
        masked = input_normalizer.redact_pii(normalized)
        slots = slot_extractor.extract_slots(masked, original_text=normalized)

        candidate = self._classify_heuristics(masked)
        if not candidate:
            candidate = await self._classify_model(masked)

        latency = (time.time() - start_time) * 1000
        context = {
            "trace_id": trace_id,
            "pii_redacted": masked != normalized,
            "original_query": user_message,
        }
        metadata = {
            "execution_time_ms": latency,
            "classifier_type": "heuristic" if candidate.confidence == 1.0 else "model",
            "model_version": "local-regex" if candidate.confidence == 1.0 else "quota-aware-router",
        }
        return confidence_evaluator.evaluate(candidate, slots, context, metadata)

    async def classify(self, user_message: str) -> Dict[str, Any]:
        descriptor = await self.classify_and_parse(user_message)
        return {
            "intent": descriptor.intent.name,
            "confidence": descriptor.intent.confidence,
            "reason": descriptor.intent.reason,
            "slots": {k: s.model_dump() for k, s in descriptor.slots.items()},
            "needs_clarification": descriptor.needs_clarification,
        }


intent_classifier = IntentClassifier()
