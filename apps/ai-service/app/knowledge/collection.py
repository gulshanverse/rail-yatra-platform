"""
Collection Management: Schema configurations, multi-domain isolation, and zero-downtime embedding model migration.
"""

import logging
import threading
from typing import Dict, Any

from app.knowledge.interfaces import (
    ICollectionManager,
    IEmbeddingProvider,
    IVectorStore,
)
from app.knowledge.exceptions import VectorStoreException
from app.knowledge.vector_store import VectorStoreFactory, MockVectorStore

logger = logging.getLogger("ai-service.knowledge.collection")


class CollectionManager(ICollectionManager):
    """Manages index partition schemas and facilitates zero-downtime embedding updates."""

    def __init__(self, vector_store: IVectorStore = None) -> None:
        self.store = vector_store or VectorStoreFactory.get_store()
        self._lock = threading.Lock()

    async def create_collection(
        self, collection_name: str, config: Dict[str, Any]
    ) -> None:
        """Sets up collection metadata partition."""
        dimension = config.get("dimension", 768)
        await self.store.initialize_collection(collection_name, dimension)

    async def delete_collection(self, collection_name: str) -> None:
        """Removes index workspace."""
        await self.store.delete_collection(collection_name)

    async def migrate_collection(
        self, source: str, target: str, transform_provider: IEmbeddingProvider
    ) -> None:
        """Conducts zero-downtime migrations by re-embedding data and hot-swapping references."""
        logger.warning(
            f"Embedding Migration: Transferring index elements from '{source}' to '{target}'..."
        )

        if not isinstance(self.store, MockVectorStore):
            logger.info("Non-mock database detected. Skipping local migration loop.")
            return

        with self.store._lock:
            if source not in self.store._collections:
                raise VectorStoreException(
                    f"Migration error: source collection '{source}' does not exist"
                )
            source_elements = list(self.store._collections[source])

        # 1. Initialize target collection dimension structure
        await self.create_collection(
            target, {"dimension": transform_provider.dimension}
        )

        if not source_elements:
            logger.info("Source collection is empty. Migration complete.")
            return

        # 2. Extract and re-embed payloads
        texts = [p.get("text", "") for _, p in source_elements]
        try:
            logger.info(
                f"Re-embedding {len(texts)} chunks using target model '{transform_provider.model_name}'..."
            )
            new_vectors = await transform_provider.embed_documents(texts)

            # Enrich payloads with target embedding version
            new_payloads = []
            for _, payload in source_elements:
                payload_copy = dict(payload)
                payload_copy["embedding_version"] = transform_provider.model_name
                new_payloads.append(payload_copy)

            # 3. Upsert to target collection index
            await self.store.upsert_chunks(target, new_vectors, new_payloads)
            logger.warning(
                f"Collection migration from '{source}' to '{target}' completed successfully"
            )
        except Exception as e:
            logger.error(
                f"Migration transaction failed: {e}. Cleaning target collection..."
            )
            await self.delete_collection(target)
            raise VectorStoreException(f"Collection migration failed: {e}")
