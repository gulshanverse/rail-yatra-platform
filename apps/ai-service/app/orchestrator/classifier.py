import logging
import json
import re
from typing import Dict, Any
from app.providers.llm import get_chat_model
from app.prompts.classifier import INTENT_CLASSIFIER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger("ai-service.orchestrator.classifier")

class IntentClassifier:
    """
    Component to identify user intent and route execution to specialized agents.
    """
    def __init__(self):
        self.llm = get_chat_model()

    async def classify(self, user_message: str) -> Dict[str, Any]:
        logger.info(f"Classifying message: '{user_message}'")
        
        messages = [
            SystemMessage(content=INTENT_CLASSIFIER_PROMPT),
            HumanMessage(content=user_message)
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            content = str(response.content).strip()
            
            # Clean possible markdown code fences from JSON output
            clean_content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE).strip()
            
            data = json.loads(clean_content)
            intent = data.get("intent", "conversation").lower()
            confidence = data.get("confidence", 0.5)
            reason = data.get("reason", "Parsed classification output.")
            
            logger.info(f"Intent classified as: {intent} (confidence: {confidence})")
            return {"intent": intent, "confidence": confidence, "reason": reason}
            
        except Exception as e:
            logger.error(f"Failed to classify intent via LLM: {e}. Running local keyword heuristics.")
            
            # Local keyword heuristics fallback
            msg = user_message.lower()
            if any(k in msg for k in ["train", "route", "schedule", "go to", "travel to", "from", "to"]):
                intent = "plan_travel"
            elif any(k in msg for k in ["recommend", "better", "compare", "score", "comfort", "rate"]):
                intent = "recommendation"
            elif any(k in msg for k in ["pnr", "ticket status", "booking status"]):
                intent = "check_pnr"
            elif any(k in msg for k in ["policy", "luggage", "refund", "faq", "rules"]):
                intent = "knowledge"
            elif any(k in msg for k in ["waitlist", "delay", "confirm", "forecast", "prediction"]):
                intent = "journey_intelligence"
            else:
                intent = "conversation"
                
            return {
                "intent": intent,
                "confidence": 0.5,
                "reason": "Fallback local classification rules."
            }

intent_classifier = IntentClassifier()
