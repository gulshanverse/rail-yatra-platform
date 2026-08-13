import logging
from typing import Dict, Any, AsyncIterator, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from app.providers.llm import get_chat_model, _invoke_with_retry

logger = logging.getLogger("ai-service.agents.base")


def extract_text_content(content: Any) -> str:
    """
    Normalizes LangChain AIMessage.content into a plain text string.

    Gemini models via LangChain may return content as:
    - A plain string: "Hello, I can help you..."
    - A list of structured content blocks:
      [{"type": "text", "text": "Hello...", "extras": {"signature": "..."}}]

    This function extracts only the human-readable text and discards
    provider metadata (extras, signatures, execution paths).
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict):
                # Extract text from {"type": "text", "text": "..."} blocks
                if block.get("type") == "text" and "text" in block:
                    text_parts.append(block["text"])
                elif "text" in block:
                    text_parts.append(block["text"])
                elif "content" in block:
                    text_parts.append(str(block["content"]))
            elif isinstance(block, str):
                text_parts.append(block)
        if text_parts:
            return "\n\n".join(text_parts)

    # Final fallback: convert to string but should rarely be reached
    return str(content)


class BaseAgent:
    """
    Base Agent class that initializes the LLM provider and defines
    standard execution interfaces for specialized travel sub-agents.
    """

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt

    @property
    def llm(self):
        return get_chat_model()

    def _prepare_messages(
        self, user_message: str, context: Optional[Dict[str, Any]] = None
    ) -> list:
        # Formulate final prompt with context if available
        context_str = ""
        if context:
            context_str = "\n## Contextual Session Variables:\n"
            for k, v in context.items():
                context_str += f"- {k}: {v}\n"

        return [
            SystemMessage(content=self.system_prompt + context_str),
            HumanMessage(content=user_message),
        ]

    async def run(
        self, user_message: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Runs the agent synchronously and returns the complete text response."""
        logger.info(f"Running agent '{self.name}'")
        messages = self._prepare_messages(user_message, context)
        model = get_chat_model()
        # Use retry wrapper to handle transient 429 quota errors
        response = await _invoke_with_retry(
            model, messages, provider="gemini", model_name="gemini-3.5-flash"
        )
        return extract_text_content(response.content)

    async def run_stream(
        self, user_message: str, context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """Runs the agent and streams the response token-by-token."""
        logger.info(f"Streaming agent '{self.name}'")
        messages = self._prepare_messages(user_message, context)
        model = get_chat_model()
        async for chunk in model.astream(messages):
            yield extract_text_content(chunk.content)


