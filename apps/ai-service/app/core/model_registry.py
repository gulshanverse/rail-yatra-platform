"""Supported LLM models and in-process quota health state."""

from dataclasses import dataclass
import time


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model: str
    priority: int
    complexity: str
    enabled: bool = True


MODEL_REGISTRY: tuple[ModelSpec, ...] = (
    ModelSpec("gemini", "gemini-3.5-flash", 10, "high"),
    ModelSpec("gemini", "gemini-3.6-flash", 20, "high"),
    ModelSpec("gemini", "gemini-3.5-flash-lite", 30, "standard"),
    ModelSpec("gemini", "gemini-3.1-flash-lite", 40, "standard"),
)

# Process-local circuit breaker. A restart clears this state, which is desirable
# because deployments should re-probe models rather than persist stale quota state.
_unavailable_until: dict[tuple[str, str], float] = {}


def mark_quota_exhausted(provider: str, model: str, retry_after: float = 60.0) -> None:
    """Temporarily remove a quota-exhausted model from routing."""
    cooldown = max(float(retry_after), 60.0)
    _unavailable_until[(provider, model)] = time.monotonic() + cooldown


def is_available(spec: ModelSpec) -> bool:
    """Return whether the model circuit is currently closed."""
    key = (spec.provider, spec.model)
    until = _unavailable_until.get(key)
    if until is None:
        return True
    if time.monotonic() >= until:
        _unavailable_until.pop(key, None)
        return True
    return False


def models_for_complexity(complexity: str) -> list[ModelSpec]:
    """Return healthy enabled models in deterministic priority order."""
    return sorted(
        (m for m in MODEL_REGISTRY if m.enabled and is_available(m)),
        key=lambda m: (0 if m.complexity == complexity else 1, m.priority),
    )
