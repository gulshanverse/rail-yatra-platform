"""
Vector Store abstraction: Mock DB with cosine similarity search and index coordination management.
"""

import logging
import threading
from typing import Dict, Any, List, Tuple

from app.knowledge.interfaces import IVectorStore
from app.knowledge.exceptions import VectorStoreException
from app.knowledge.config import knowledge_settings

logger = logging.getLogger("ai-service.knowledge.vector_store")


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates vector similarity metric between two floating arrays."""
    if len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = sum(a * a for a in v1) ** 0.5
    norm_b = sum(b * b for b in v2) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class MockVectorStore(IVectorStore):
    """In-memory collection dictionary simulating production database query indexings."""

    def __init__(self) -> None:
        # collection_name -> list of (vector, payload)
        self._collections: Dict[str, List[Tuple[List[float], Dict[str, Any]]]] = {}
        self._lock = threading.Lock()

    async def initialize_collection(self, collection_name: str, dimension: int) -> None:
        with self._lock:
            if collection_name not in self._collections:
                self._collections[collection_name] = []
                logger.info(
                    f"Initialized mock collection space '{collection_name}' (dimension: {dimension})"
                )

    async def delete_collection(self, collection_name: str) -> None:
        with self._lock:
            self._collections.pop(collection_name, None)
            logger.info(f"Deleted mock collection space '{collection_name}'")

    async def upsert_chunks(
        self,
        collection_name: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
    ) -> None:
        if len(vectors) != len(payloads):
            raise VectorStoreException(
                "Vectors list size must match payloads list size"
            )

        with self._lock:
            if collection_name not in self._collections:
                self._collections[collection_name] = []

            for vec, payload in zip(vectors, payloads):
                # Ensure we override if matching chunk_id already exists
                chunk_id = payload.get("chunk_id")
                # Remove old instance if exists
                self._collections[collection_name] = [
                    (v, p)
                    for v, p in self._collections[collection_name]
                    if p.get("chunk_id") != chunk_id
                ]
                self._collections[collection_name].append((vec, payload))

            logger.info(
                f"Upserted {len(vectors)} chunks into mock collection '{collection_name}'"
            )

    async def search_chunks(
        self,
        collection_name: str,
        query_vector: List[float],
        filter_metadata: Dict[str, Any],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            collection = self._collections.get(collection_name)
            if not collection:
                return []

            results = []
            for vec, payload in collection:
                # Apply simple metadata filter checks
                match = True
                for k, v in filter_metadata.items():
                    if payload.get(k) != v:
                        match = False
                        break

                if match:
                    sim = cosine_similarity(query_vector, vec)
                    # Enrich payload with similarity score
                    result_item = dict(payload)
                    result_item["similarity_score"] = float(round(sim, 4))
                    results.append(result_item)

            # Sort by similarity score descending
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return results[:limit]


class VectorStoreFactory:
    """Factory producing vector store connector engines."""

    _instance: MockVectorStore = None
    _lock = threading.Lock()

    @classmethod
    def get_store(cls, active_db: str = None) -> IVectorStore:
        """Returns single connector wrapper instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = MockVectorStore()
            return cls._instance


class IndexManager:
    """Coordinates batch segment indexing, reindexing, and vector collection updates."""

    def __init__(self, vector_store: IVectorStore = None) -> None:
        self.store = vector_store or VectorStoreFactory.get_store()
        self.active_collection = "railway_knowledge"

    async def initialize(self) -> None:
        """Sets up collection schemas."""
        await self.store.initialize_collection(
            self.active_collection, knowledge_settings.EMBEDDING_DIMENSION
        )

    async def index_batch(
        self, vectors: List[List[float]], payloads: List[Dict[str, Any]]
    ) -> None:
        """Pushes updates directly to vector index collections."""
        await self.store.upsert_chunks(self.active_collection, vectors, payloads)

    async def remove_document_chunks(self, doc_id: str) -> None:
        """Deletes indexing records for specific document keys (rollback helper)."""
        # Read collection, filter out and overwrite
        # For mock store we can access collections directly or implement interface delete
        if isinstance(self.store, MockVectorStore):
            with self.store._lock:
                if self.active_collection in self.store._collections:
                    self.store._collections[self.active_collection] = [
                        (v, p)
                        for v, p in self.store._collections[self.active_collection]
                        if p.get("parent_document") != doc_id
                    ]
                    logger.info(f"Removed chunks for document {doc_id} from collection")
        else:
            # Future DB cleanups will execute collection deletes by metadata query filters
            pass

    async def trigger_full_reindex(
        self, all_payloads: List[Tuple[List[float], Dict[str, Any]]]
    ) -> None:
        """Executes a clean indexing swap segment operation."""
        temp_collection = f"{self.active_collection}_rebuild"
        await self.store.initialize_collection(
            temp_collection, knowledge_settings.EMBEDDING_DIMENSION
        )

        vectors = [x[0] for x in all_payloads]
        payloads = [x[1] for x in all_payloads]

        await self.store.upsert_chunks(temp_collection, vectors, payloads)

        # Hot-swap collection pointers
        await self.store.delete_collection(self.active_collection)
        await self.store.initialize_collection(
            self.active_collection, knowledge_settings.EMBEDDING_DIMENSION
        )
        await self.store.upsert_chunks(self.active_collection, vectors, payloads)
        await self.store.delete_collection(temp_collection)
        logger.warning("Reindexing complete. Collection hot-swap succeeded.")
