import asyncio
from types import SimpleNamespace

import pytest

from app.agents import base
from app.core.model_registry import ModelSpec


class QuotaModel:
    def __init__(self, message: str):
        self.message = message

    async def ainvoke(self, messages):
        raise RuntimeError("429 RESOURCE_EXHAUSTED: retry in 2s")


class HealthyModel:
    async def ainvoke(self, messages):
        return SimpleNamespace(content="Fallback model answered successfully.")


@pytest.mark.anyio
async def test_run_with_failover_switches_immediately(monkeypatch):
    specs = [
        ModelSpec("gemini", "primary", 1, "high"),
        ModelSpec("gemini", "fallback", 2, "high"),
    ]
    models = {"primary": QuotaModel("primary"), "fallback": HealthyModel()}
    monkeypatch.setattr(base, "_candidate_models", lambda _: specs)
    monkeypatch.setattr(base, "get_chat_model", lambda provider, model_name: models[model_name])

    response = await base._run_with_failover([])

    assert response.content == "Fallback model answered successfully."


@pytest.mark.anyio
async def test_run_with_failover_skips_hung_primary(monkeypatch):
    specs = [
        ModelSpec("gemini", "primary", 1, "high"),
        ModelSpec("gemini", "fallback", 2, "high"),
    ]

    class HungModel:
        async def ainvoke(self, messages):
            await asyncio.sleep(60)

    models = {"primary": HungModel(), "fallback": HealthyModel()}
    monkeypatch.setattr(base, "MODEL_REQUEST_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(base, "_candidate_models", lambda _: specs)
    monkeypatch.setattr(base, "get_chat_model", lambda provider, model_name: models[model_name])

    response = await base._run_with_failover([])

    assert response.content == "Fallback model answered successfully."


@pytest.mark.anyio
async def test_run_with_failover_raises_when_all_models_are_exhausted(monkeypatch):
    specs = [
        ModelSpec("gemini", "primary", 1, "high"),
        ModelSpec("gemini", "fallback", 2, "high"),
    ]
    monkeypatch.setattr(base, "_candidate_models", lambda _: specs)
    monkeypatch.setattr(base, "get_chat_model", lambda provider, model_name: QuotaModel(model_name))

    with pytest.raises(base.QuotaExhaustedError):
        await base._run_with_failover([])


@pytest.mark.anyio
async def test_stream_fails_over_before_first_token(monkeypatch):
    specs = [
        ModelSpec("gemini", "primary", 1, "high"),
        ModelSpec("gemini", "fallback", 2, "high"),
    ]

    class StreamQuotaModel:
        async def astream(self, messages):
            raise RuntimeError("429 RESOURCE_EXHAUSTED: retry in 2s")
            yield  # pragma: no cover

    class StreamHealthyModel:
        async def astream(self, messages):
            yield SimpleNamespace(content="fallback stream")

    models = {"primary": StreamQuotaModel(), "fallback": StreamHealthyModel()}
    monkeypatch.setattr(base, "_candidate_models", lambda _: specs)
    monkeypatch.setattr(base, "get_chat_model", lambda provider, model_name: models[model_name])

    agent = base.BaseAgent("test", "test")
    result = [chunk async for chunk in agent.run_stream("hello")]

    assert result == ["fallback stream"]
