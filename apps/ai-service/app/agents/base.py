import logging
from typing import Any, AsyncIterator, Dict, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.providers.llm import _invoke_with_retry, get_chat_model

logger = logging.getLogger("ai-service.agents.base")


def extract_text_content(content: Any) -> str:
    """Return only human-readable assistant text from provider/LangChain content.

    Gemini responses can be strings, structured text blocks, dictionaries, or
    empty values. Provider metadata such as signatures and extras must never
    reach the chat UI.
    """
    if content is None:
        return ""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, dict):
        for key in ("text", "content", "reply", "message"):
            value = content.get(key)
            if isinstance(value, str):
                return value.strip()
        return ""

    if isinstance(content, list):
        text_parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                if block.strip():
                    text_parts.append(block.strip())
                continue
            if isinstance(block, dict):
                value = block.get("text")
                if not isinstance(value, str):
                    value = block.get("content")
                if isinstance(value, str) and value.strip():
                    text_parts.append(value.strip())
        return "\n\n".join(text_parts)

    return str(content).strip()


class BaseAgent:
    """Base agent with shared LLM setup and response normalization."""

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt

    @property
    def llm(self):
        return get_chat_model()

    def _prepare_messages(
        self, user_message: str, context: Optional[Dict[str, Any]] = None
    ) -> list:
        context_str = ""
        if context:
            context_str = "\n## Contextual Session Variables:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"

        return [
            SystemMessage(content=self.system_prompt + context_str),
            HumanMessage(content=user_message),
        ]

    async def run(
        self, user_message: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        logger.info("Running agent '%s'", self.name)
        messages = self._prepare_messages(user_message, context)
        model = get_chat_model()
        response = await _invoke_with_retry(
            model, messages, provider="gemini", model_name="gemini-3.5-flash"
        )
        return extract_text_content(response.content)

    async def run_stream(
        self, user_message: str, context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        logger.info("Streaming agent '%s'", self.name)
        messages = self._prepare_messages(user_message, context)
        model = get_chat_model()
        async for chunk in model.astream(messages):
            text = extract_text_content(chunk.content)
            if text:
                yield text
