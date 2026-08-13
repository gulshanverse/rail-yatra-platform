"""Supported LLM models and routing metadata."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model: str
    priority: int
    complexity: str
    enabled: bool = True


# Ordered by quality/capability first. The router skips models that are
# disabled or currently in cooldown/quota-exhausted state.
MODEL_REGISTRY: tuple[ModelSpec, ...] = (
    ModelSpec("gemini", "gemini-3.5-flash", 10, "high"),
    ModelSpec("gemini", "gemini-3.6-flash", 20, "high"),
    ModelSpec("gemini", "gemini-3.5-flash-lite", 30, "standard"),
    ModelSpec("gemini", "gemini-3.1-flash-lite", 40, "standard"),
)


def models_for_complexity(complexity: str) -> list[ModelSpec]:
    """Return enabled models in deterministic priority order."""
    return sorted(
        (m for m in MODEL_REGISTRY if m.enabled),
        key=lambda m: (0 if m.complexity == complexity else 1, m.priority),
    )
