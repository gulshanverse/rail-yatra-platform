import logging
import json
import time
from typing import List, Optional, Any, Iterator, AsyncIterator
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, AIMessageChunk
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from langchain_core.callbacks.manager import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from app.config.config import settings

logger = logging.getLogger("ai-service.providers")

class MockChatModel(BaseChatModel):
    provider_name: str = "mock-provider"
    model_name: str = "mock-model"

    def _llm_type(self) -> str:
        return "mock-chat-model"

    def _generate_mock_response(self, messages: List[BaseMessage]) -> str:
        # Simple rule-based mock responses based on user query
        user_query = ""
        system_prompt = ""
        
        for msg in messages:
            if msg.type == "human":
                user_query = str(msg.content).lower()
            elif msg.type == "system":
                system_prompt = str(msg.content).lower()

        # Check for intent classification request first
        if "target intents" in system_prompt or "intent classification" in system_prompt:
            intent = "conversation"
            reason = "Greetings or general query"
            if any(k in user_query for k in ["train", "route", "schedule", "go to", "travel to", "from", "to"]):
                intent = "plan_travel"
                reason = "Inquiry regarding train schedule or route planning"
            elif any(k in user_query for k in ["recommend", "better", "compare", "score", "comfort", "rate"]):
                intent = "recommendation"
                reason = "Comparing train choices or travel tiers"
            elif any(k in user_query for k in ["pnr", "ticket status", "booking status"]):
                intent = "check_pnr"
                reason = "Inquiry regarding checking a ticket PNR status"
            elif any(k in user_query for k in ["policy", "luggage", "refund", "faq", "rules"]):
                intent = "knowledge"
                reason = "General query about railway procedures or guidelines"
            elif any(k in user_query for k in ["waitlist", "delay", "confirm", "forecast", "prediction"]):
                intent = "journey_intelligence"
                reason = "Predictive intelligence check"

            return json.dumps({
                "intent": intent,
                "confidence": 0.96,
                "reason": reason
            })

        # Standard agent mock responses
        if "specialized travel decision agent" in system_prompt or "travel_decision" in system_prompt or "plan_travel" in system_prompt:
            return (
                "### Proposed Route Options\n\n"
                "I found the following optimal train routes for your journey:\n\n"
                "| Train Number / Name | Departure | Arrival | Duration | Available Classes | Status |\n"
                "|:---|:---|:---|:---|:---|:---|\n"
                "| **12002 / Bhopal Shatabdi** | 06:00 | 14:40 | 8h 40m | CC, EC | **Available (CNF)** |\n"
                "| **12626 / Kerala Express** | 11:25 | 20:10 | 8h 45m | SL, 3A, 2A, 1A | **WL 12 (Chance: 88%)** |\n\n"
                "> [!TIP]\n"
                "> Shatabdi is recommended for punctuality (Avg. Delay < 15 mins)."
            )

        if "smart recommendation agent" in system_prompt or "recommendation" in system_prompt:
            return (
                "### Smart Recommendation Matrix\n\n"
                "Here is the evaluation matrix for your alternatives:\n\n"
                "- **Shatabdi Express (Score: 92/100)**: Excellent comfort, fast speed, low delay risk, but higher price. Best value.\n"
                "- **Kerala Express (Score: 78/100)**: Budget-friendly, standard sleeping berths, but higher risk of 30-minute delays.\n\n"
                "**Confidence Score**: 95%\n"
                "**Pros**: Fast transit, meals included in Shatabdi.\n"
                "**Cons**: Shatabdi does not have sleeper berths if traveling overnight."
            )

        if "ticket confirmation prediction agent" in system_prompt or "prediction" in system_prompt:
            return (
                "### Confirmation Probability Forecast\n\n"
                "- **Current PNR Status**: WL 14 (3AC Class)\n"
                "- **Confirmation Chance**: **84% (High)**\n"
                "- **Historical Clearance**: Waitlist up to WL 25 on this train usually clears 92% of the time in this season.\n"
                "- **Average Delay**: 25 minutes late over the last 15 runs.\n\n"
                "> [!NOTE]\n"
                "> You have a high probability of boarding confirmation. No need to look for alternate flights yet."
            )

        if "knowledge retrieval agent" in system_prompt or "knowledge" in system_prompt:
            return (
                "### Railway Luggage and Refund Policies (RAG)\n\n"
                "Based on the vector knowledge base:\n"
                "1. **Luggage Limits**: A passenger in 3AC can carry up to 40 kg of luggage free of charge.\n"
                "2. **Refund Rules**: For confirmed tickets cancelled 48 hours prior to train departure, the flat fee is Rs. 180 for 3AC."
            )

        return (
            "Hello! I am **RailYatra AI**, your premium Travel Intelligence assistant. How can I help you plan your journey, "
            "check PNR status, or optimize your travel decisions today?"
        )

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        response_text = self._generate_mock_response(messages)
        message = AIMessage(content=response_text)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        response_text = self._generate_mock_response(messages)
        # Yield word by word with short delay to simulate streaming
        words = response_text.split(" ")
        for i, word in enumerate(words):
            chunk_content = word + (" " if i < len(words) - 1 else "")
            chunk = AIMessageChunk(content=chunk_content)
            yield ChatGenerationChunk(message=chunk)
            time.sleep(0.01)  # 10ms delay per word

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        response_text = self._generate_mock_response(messages)
        words = response_text.split(" ")
        for i, word in enumerate(words):
            chunk_content = word + (" " if i < len(words) - 1 else "")
            chunk = AIMessageChunk(content=chunk_content)
            yield ChatGenerationChunk(message=chunk)
            # Yield control back to event loop
            import asyncio
            await asyncio.sleep(0.01)


def get_chat_model(provider: str | None = None, model_name: str | None = None) -> BaseChatModel:
    """
    Factory function returning the correct ChatModel based on provider name.
    If credentials are missing or mock mode is enabled, returns MockChatModel.
    """
    prov = provider or settings.DEFAULT_PROVIDER
    model = model_name or settings.DEFAULT_MODEL

    logger.info(f"Initializing ChatModel for provider: {prov}, model: {model}")

    if settings.ENABLE_MOCK_LLM:
        logger.info("Using MockChatModel (Mock Mode explicitly enabled)")
        return MockChatModel(provider_name="mock", model_name="mock")

    try:
        if prov == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("Missing OPENAI_API_KEY")
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(openai_api_key=settings.OPENAI_API_KEY, model=model)
            
        elif prov == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("Missing ANTHROPIC_API_KEY")
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(anthropic_api_key=settings.ANTHROPIC_API_KEY, model=model)
            
        elif prov == "gemini":
            if not settings.GOOGLE_API_KEY:
                raise ValueError("Missing GOOGLE_API_KEY")
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(google_api_key=settings.GOOGLE_API_KEY, model=model)
            
        elif prov == "openrouter":
            if not settings.OPENROUTER_API_KEY:
                raise ValueError("Missing OPENROUTER_API_KEY")
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                openai_api_key=settings.OPENROUTER_API_KEY,
                model=model,
                base_url="https://openrouter.ai/api/v1"
            )
            
        elif prov == "local":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                openai_api_key="local-placeholder",
                model=model,
                base_url=settings.LOCAL_LLM_BASE_URL
            )
            
        else:
            raise ValueError(f"Unknown provider '{prov}'")
            
    except Exception as e:
        logger.warning(f"Failed to initialize ChatModel for {prov}: {e}. Falling back to MockChatModel.")
        return MockChatModel(provider_name="mock-fallback", model_name="mock-fallback")
