import asyncio

from app.api.endpoints import _classify_ai_error


def test_classify_timeout_error():
    code, message = _classify_ai_error(asyncio.TimeoutError())
    assert code == "AI_WORKFLOW_TIMEOUT"
    assert "too long" in message


def test_classify_rate_limit_error():
    code, message = _classify_ai_error(RuntimeError("provider returned 429 rate limit"))
    assert code == "AI_PROVIDER_RATE_LIMIT"
    assert "rate-limited" in message


def test_classify_configuration_error_without_leaking_secret():
    secret = "sk-secret-value"
    code, message = _classify_ai_error(RuntimeError(f"401 invalid api key {secret}"))
    assert code == "AI_PROVIDER_CONFIGURATION"
    assert secret not in message
    assert "configuration" in message


def test_classify_provider_timeout():
    code, message = _classify_ai_error(RuntimeError("provider request timed out"))
    assert code == "AI_PROVIDER_TIMEOUT"
    assert "timed out" in message


def test_classify_unknown_error_safely():
    secret = "internal-token-123"
    code, message = _classify_ai_error(RuntimeError(f"unexpected failure {secret}"))
    assert code == "AI_WORKFLOW_ERROR"
    assert secret not in message
