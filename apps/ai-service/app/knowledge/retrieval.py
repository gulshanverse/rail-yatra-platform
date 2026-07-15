"""
Retrieval Platform: Routing Policy engine and Retrieval Coordinator wrapper.
"""

import logging
from typing import Dict, Any, List, Tuple

from app.knowledge.interfaces import (
    IRetrievalPolicy,
    IRetrievalCoordinator,
    IEmbeddingProvider,
    IVectorStore,
)
from app.knowledge.exceptions import RetrievalException
from app.knowledge.embedding import EmbeddingFactory
from app.knowledge.vector_store import VectorStoreFactory

logger = logging.getLogger("ai-service.knowledge.retrieval")


class RetrievalPolicy(IRetrievalPolicy):
    """Filters queries and configures search arguments according to policy definitions."""

    def apply_policy(
        self, query: str, config: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        policy_type = config.get("policy_type", "hybrid").lower()
        metadata_filters = {}

        # Enforce target category filters
        if "category" in config:
            metadata_filters["category"] = config["category"]

        # Enforce temporal filters
        if "last_updated_after" in config:
            metadata_filters["updated_at"] = config["last_updated_after"]

        # Enforce tenant/security isolation scope
        if "security_classification" in config:
            metadata_filters["security_classification"] = config[
                "security_classification"
            ]

        return policy_type, metadata_filters


class RetrievalCoordinator(IRetrievalCoordinator):
    """Orchestrates embedding generation, vector store querying, and score ranking."""

    def __init__(
        self,
        embedding_provider: IEmbeddingProvider = None,
        vector_store: IVectorStore = None,
    ) -> None:
        self.embedding_provider = embedding_provider or EmbeddingFactory.get_provider()
        self.vector_store = vector_store or VectorStoreFactory.get_store()
        self.policy_engine = RetrievalPolicy()
        self.active_collection = "railway_knowledge"

    async def retrieve(
        self, query: str, policy_name: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        try:
            # Load mock policy config
            policy_config = {"policy_type": policy_name}

            # 1. Apply policy filters
            policy_type, filters = self.policy_engine.apply_policy(query, policy_config)
            logger.info(
                f"Retrieval executing query under policy '{policy_type}' with filters: {filters}"
            )

            # 2. Get query vector
            query_vector = await self.embedding_provider.embed_query(query)

            # 3. Query the store wrapper
            results = await self.vector_store.search_chunks(
                collection_name=self.active_collection,
                query_vector=query_vector,
                filter_metadata=filters,
                limit=limit,
            )

            return results
        except Exception as e:
            raise RetrievalException(f"Retrieval coordinator operation failed: {e}")
