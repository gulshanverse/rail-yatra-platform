import logging
from typing import Dict, Any, AsyncIterator, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from app.providers.llm import get_chat_model

logger = logging.getLogger("ai-service.agents.base")


class BaseAgent:
    """
    Base Agent class that initializes the LLM provider and defines
    standard execution interfaces for specialized travel sub-agents.
    """

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = get_chat_model()

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
        response = await self.llm.ainvoke(messages)
        return str(response.content)

    async def run_stream(
        self, user_message: str, context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """Runs the agent and streams the response token-by-token."""
        logger.info(f"Streaming agent '{self.name}'")
        messages = self._prepare_messages(user_message, context)
        async for chunk in self.llm.astream(messages):
            yield str(chunk.content)
