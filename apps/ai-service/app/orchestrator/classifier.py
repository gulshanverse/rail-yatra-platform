import logging
import json
import re
import time
from typing import Dict, Any, Optional

from app.providers.llm import get_chat_model
from app.prompts.classifier import INTENT_CLASSIFIER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

from app.orchestrator.normalizer import input_normalizer
from app.orchestrator.slot_extractor import slot_extractor
from app.orchestrator.evaluator import confidence_evaluator
from app.orchestrator.types import IntentDescriptor, IntentCandidate

logger = logging.getLogger("ai-service.orchestrator.classifier")


class IntentClassifier:
    """
    Component to identify user intent and route execution to specialized agents.
    Implements normalizer, heuristic routing, model classification, slot extraction,
    and confidence evaluation.
    """

    def __init__(self):
        # Lazy initialization of LLM
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_chat_model()
        return self._llm

    def _classify_heuristics(self, text: str) -> Optional[IntentCandidate]:
        """
        Executes local heuristic regex-based classification for fast-path routing.
        """
        msg = text.lower()
        intent = None
        reason = "Heuristic regex match"

        # Check PNR check patterns
        if any(k in msg for k in ["pnr", "ticket status", "booking status"]):
            intent = "check_pnr"
        # Check plan travel patterns
        elif any(
            k in msg
            for k in ["train", "route", "schedule", "go to", "travel to", "from", "to"]
        ):
            intent = "plan_travel"
        # Check journey intelligence patterns
        elif any(
            k in msg for k in ["waitlist", "delay", "confirm", "forecast", "prediction"]
        ):
            intent = "journey_intelligence"
        # Check knowledge patterns
        elif any(k in msg for k in ["policy", "luggage", "refund", "faq", "rules"]):
            intent = "knowledge"
        # Check recommendation patterns
        elif any(
            k in msg
            for k in ["recommend", "better", "compare", "score", "comfort", "rate"]
        ):
            intent = "recommendation"

        if intent:
            logger.info(f"Heuristic classifier matched: {intent}")
            return IntentCandidate(name=intent, confidence=1.0, reason=reason)

        return None

    async def _classify_model(self, text: str) -> IntentCandidate:
        """
        Runs LLM-based multi-class classification for complex queries.
        """
        logger.info(f"Sending text to LLM for classification: '{text}'")
        messages = [
            SystemMessage(content=INTENT_CLASSIFIER_PROMPT),
            HumanMessage(content=text),
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = str(response.content).strip()

            # Clean possible markdown code fences from JSON output
            clean_content = re.sub(
                r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE
            ).strip()

            data = json.loads(clean_content)
            intent = data.get("intent", "conversation").lower()
            confidence = float(data.get("confidence", 0.5))
            reason = data.get("reason", "Parsed classification output.")

            logger.info(
                f"Model classifier returned: {intent} (confidence: {confidence})"
            )
            return IntentCandidate(name=intent, confidence=confidence, reason=reason)

        except Exception as e:
            logger.error(
                f"LLM classification failed: {e}. Falling back to default heuristics."
            )
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
        """
        Executes the full semantic parsing pipeline:
        Normalization -> Heuristics/Model Classification -> Slot Extraction -> Evaluation.
        """
        start_time = time.time()

        # 1. Normalize
        normalized = input_normalizer.normalize(user_message)

        # 2. Mask PII for the model prompt
        masked = input_normalizer.redact_pii(normalized)

        # 3. Extract Slots (from original normalized text to preserve codes/PNRs before masking)
        slots = slot_extractor.extract_slots(masked, original_text=normalized)

        # 4. Classify (Heuristics with fallback to Model)
        candidate = self._classify_heuristics(masked)
        if not candidate:
            candidate = await self._classify_model(masked)

        # 5. Evaluate and build descriptor
        latency = (time.time() - start_time) * 1000
        context = {
            "trace_id": trace_id,
            "pii_redacted": masked != normalized,
            "original_query": user_message,
        }
        metadata = {
            "execution_time_ms": latency,
            "classifier_type": "heuristic" if candidate.confidence == 1.0 else "model",
            "model_version": "gemini-3.5-flash"
            if candidate.confidence != 1.0
            else "local-regex",
        }

        descriptor = confidence_evaluator.evaluate(candidate, slots, context, metadata)
        return descriptor

    async def classify(self, user_message: str) -> Dict[str, Any]:
        """
        Legacy/Backward-compatible endpoint for existing graph nodes and tests.
        """
        descriptor = await self.classify_and_parse(user_message)
        return {
            "intent": descriptor.intent.name,
            "confidence": descriptor.intent.confidence,
            "reason": descriptor.intent.reason,
            "slots": {k: s.model_dump() for k, s in descriptor.slots.items()},
            "needs_clarification": descriptor.needs_clarification,
        }


intent_classifier = IntentClassifier()
