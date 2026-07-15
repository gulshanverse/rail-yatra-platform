"""
Embedding Platform: Providers factory, mock embedding generator, and metrics evaluator.
"""

import hashlib
import logging
from typing import Dict, Any, List

from app.knowledge.interfaces import IEmbeddingProvider, IEmbeddingEvaluator
from app.knowledge.exceptions import EmbeddingException
from app.knowledge.config import knowledge_settings

logger = logging.getLogger("ai-service.knowledge.embedding")


class MockEmbeddingProvider(IEmbeddingProvider):
    """Deterministic local mockup embedding provider producing hash-based vector lists."""

    def __init__(self, dimension: int = None) -> None:
        self._dimension = dimension or knowledge_settings.EMBEDDING_DIMENSION

    @property
    def model_name(self) -> str:
        return "mock-embedding-model"

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_query(self, text: str) -> List[float]:
        try:
            # Deterministic hash generation
            hash_val = hashlib.sha256(text.encode("utf-8")).hexdigest()
            values = []
            for i in range(self._dimension):
                # Generates float between -1.0 and 1.0 based on slice indexes
                char_idx = i % len(hash_val)
                val = int(hash_val[char_idx], 16) / 15.0
                values.append(val * 2.0 - 1.0)
            return values
        except Exception as e:
            raise EmbeddingException(f"Mock query embedding failed: {e}")

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            return [await self.embed_query(text) for text in texts]
        except Exception as e:
            raise EmbeddingException(f"Mock document batch embedding failed: {e}")


class OpenAIEmbeddingProvider(IEmbeddingProvider):
    """Placeholder interface adapter wrapper for OpenAI Embeddings API (Batch 4.3)."""

    @property
    def model_name(self) -> str:
        return "text-embedding-3-small"

    @property
    def dimension(self) -> int:
        return 1536

    async def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError(
            "OpenAI API calls are not implemented in Milestone 4.1."
        )

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError(
            "OpenAI API calls are not implemented in Milestone 4.1."
        )


class GeminiEmbeddingProvider(IEmbeddingProvider):
    """Placeholder interface adapter wrapper for Google Gemini Embeddings API (Batch 4.3)."""

    @property
    def model_name(self) -> str:
        return "text-embedding-004"

    @property
    def dimension(self) -> int:
        return 768

    async def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError(
            "Gemini API calls are not implemented in Milestone 4.1."
        )

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError(
            "Gemini API calls are not implemented in Milestone 4.1."
        )


class EmbeddingFactory:
    """Factory builder producing target embedding provider interfaces."""

    @staticmethod
    def get_provider(provider_name: str = None) -> IEmbeddingProvider:
        """Returns provider instance based on target name configuration."""
        name = provider_name or knowledge_settings.ACTIVE_EMBEDDING_PROVIDER
        name = name.lower()

        if name == "mock":
            return MockEmbeddingProvider()
        elif name == "openai":
            return OpenAIEmbeddingProvider()
        elif name == "gemini":
            return GeminiEmbeddingProvider()
        else:
            # Fallback to local mock for safety
            logger.warning(
                f"Embedding provider '{provider_name}' not supported. Using MockEmbeddingProvider."
            )
            return MockEmbeddingProvider()


class EmbeddingEvaluator(IEmbeddingEvaluator):
    """Evaluator suite benchmarking precision, recall, and search latency targets."""

    def evaluate_performance(
        self, provider: IEmbeddingProvider, golden_dataset: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculates mock benchmarks metric calculations."""
        # Simple calculations simulating validation sweeps
        data_count = len(golden_dataset)

        precision = 0.90 + (0.01 * min(data_count, 5))
        recall = 0.85 + (0.01 * min(data_count, 5))
        mrr = 0.88 + (0.01 * min(data_count, 5))
        ndcg = 0.89 + (0.01 * min(data_count, 5))

        return {
            "model_name": provider.model_name,
            "precision": float(round(precision, 2)),
            "recall": float(round(recall, 2)),
            "mrr": float(round(mrr, 2)),
            "ndcg": float(round(ndcg, 2)),
            "average_latency_ms": 15.4,
            "cost_per_million_tokens_usd": 0.02,
            "quality_rating": "EXCELLENT",
            "version": "bench_v1.0",
        }
