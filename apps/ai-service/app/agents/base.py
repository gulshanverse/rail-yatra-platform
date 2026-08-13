import logging
import os
import re
from typing import Any, AsyncIterator, Dict, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.model_registry import (
    ModelSpec,
    mark_quota_exhausted,
    models_for_complexity,
)
from app.providers.llm import QuotaExhaustedError, get_chat_model

logger = logging.getLogger("ai-service.agents.base")


def extract_text_content(content: Any) -> str:
    """Return only human-readable assistant text from provider/LangChain content."""
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
                value = block.get("text") or block.get("content")
                if isinstance(value, str) and value.strip():
                    text_parts.append(value.strip())
        return "\n\n".join(text_parts)
    return str(content).strip()


def _candidate_models(complexity: str = "high") -> list[ModelSpec]:
    """Build the ordered failover pool from supported and configured providers."""
    candidates = models_for_complexity(complexity)
    optional = (
        ("openai", os.getenv("OPENAI_FALLBACK_MODEL")),
        ("anthropic", os.getenv("ANTHROPIC_FALLBACK_MODEL")),
        ("openrouter", os.getenv("OPENROUTER_FALLBACK_MODEL")),
    )
    priority = max((item.priority for item in candidates), default=0) + 10
    for provider, model in optional:
        if model and model.strip():
            candidates.append(ModelSpec(provider, model.strip(), priority, "standard"))
            priority += 10
    return candidates


async def _run_with_failover(messages: list, complexity: str = "high") -> Any:
    """Call models in priority order and switch immediately on quota exhaustion."""
    last_quota_error: QuotaExhaustedError | None = None
    for spec in _candidate_models(complexity):
        try:
            model = get_chat_model(provider=spec.provider, model_name=spec.model)
            response = await model.ainvoke(messages)
            logger.info("LLM request served by %s/%s", spec.provider, spec.model)
            return response
        except Exception as exc:
            if isinstance(exc, ValueError):
                logger.warning("Skipping unavailable model %s/%s: %s", spec.provider, spec.model, exc)
                continue
            if not _is_quota_error(exc):
                raise
            retry_after = _extract_retry_delay(exc)
            last_quota_error = QuotaExhaustedError(spec.provider, spec.model, retry_after)
            mark_quota_exhausted(spec.provider, spec.model, retry_after)
            logger.warning(
                "Model %s/%s quota exhausted; switching immediately",
                spec.provider,
                spec.model,
            )

    if last_quota_error:
        raise last_quota_error
    raise RuntimeError("No enabled LLM model is available")


def _is_quota_error(exc: Exception) -> bool:
    text = str(exc).upper()
    return "429" in text or "RESOURCE_EXHAUSTED" in text or "QUOTA" in text


def _extract_retry_delay(exc: Exception) -> float:
    text = str(exc)
    if re.search(r"per\s*day|daily|RPD", text, re.IGNORECASE):
        return 24 * 60 * 60
    match = re.search(r"retry in ([\d.]+)s", text, re.IGNORECASE)
    return float(match.group(1)) if match else 60.0


class BaseAgent:
    """Base agent with shared LLM setup, normalization, and model failover."""

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
        response = await _run_with_failover(messages)
        return extract_text_content(response.content)

    async def run_stream(
        self, user_message: str, context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        logger.info("Streaming agent '%s'", self.name)
        messages = self._prepare_messages(user_message, context)

        for spec in _candidate_models("high"):
            emitted_text = False
            try:
                model = get_chat_model(provider=spec.provider, model_name=spec.model)
                logger.info("Streaming with %s/%s", spec.provider, spec.model)
                async for chunk in model.astream(messages):
                    text = extract_text_content(chunk.content)
                    if text:
                        emitted_text = True
                        yield text
                return
            except ValueError as exc:
                logger.warning("Skipping unavailable streaming model %s/%s: %s", spec.provider, spec.model, exc)
                continue
            except Exception as exc:
                if not _is_quota_error(exc):
                    raise
                if emitted_text:
                    raise
                retry_after = _extract_retry_delay(exc)
                mark_quota_exhausted(spec.provider, spec.model, retry_after)
                logger.warning(
                    "Streaming model %s/%s quota exhausted before output; switching",
                    spec.provider,
                    spec.model,
                )

        raise QuotaExhaustedError("router", "all-configured-models")
