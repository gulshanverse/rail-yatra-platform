"""
Registry and Version controllers for sources, compatibility matrices, and datasets.
"""

import logging
import threading
from typing import Dict, List, Any, Optional

from app.knowledge.interfaces import IKnowledgeSource, IKnowledgeSourceRegistry
from app.knowledge.exceptions import KnowledgeSourceException, VersionMismatchException

logger = logging.getLogger("ai-service.knowledge.registry")


class KnowledgeSourceRegistry(IKnowledgeSourceRegistry):
    """Registry locator for dynamic and static knowledge connectors."""

    def __init__(self) -> None:
        self._sources: Dict[str, IKnowledgeSource] = {}
        self._lock = threading.Lock()

    def register_source(self, source: IKnowledgeSource) -> None:
        with self._lock:
            self._sources[source.source_id] = source
            logger.info(f"Registered knowledge source: {source.source_id}")

    def deregister_source(self, source_id: str) -> None:
        with self._lock:
            if source_id in self._sources:
                self._sources.pop(source_id)
                logger.info(f"Deregistered knowledge source: {source_id}")

    def get_source(self, source_id: str) -> IKnowledgeSource:
        with self._lock:
            if source_id not in self._sources:
                raise KnowledgeSourceException(
                    f"Knowledge source {source_id} not registered"
                )
            return self._sources[source_id]

    def list_sources(self) -> List[str]:
        with self._lock:
            return list(self._sources.keys())


class VersionManager:
    """Verifies schema structure boundaries and detects model size configuration drifts."""

    def __init__(
        self,
        index_version: str = "idx_v1",
        schema_version: str = "sch_v1",
        embedding_version: str = "emb_v1",
        chunk_version: str = "chk_v1",
    ) -> None:
        self.index_version = index_version
        self.schema_version = schema_version
        self.embedding_version = embedding_version
        self.chunk_version = chunk_version
        self._lock = threading.Lock()

    def get_version_matrix(self) -> Dict[str, str]:
        """Returns active versioning configurations."""
        with self._lock:
            return {
                "index_version": self.index_version,
                "schema_version": self.schema_version,
                "embedding_version": self.embedding_version,
                "chunk_version": self.chunk_version,
            }

    def validate_compatibility(self, other_matrix: Dict[str, str]) -> bool:
        """Determines if target matrix values align with systems configurations."""
        with self._lock:
            return (
                self.index_version == other_matrix.get("index_version")
                and self.schema_version == other_matrix.get("schema_version")
                and self.embedding_version == other_matrix.get("embedding_version")
                and self.chunk_version == other_matrix.get("chunk_version")
            )


class DatasetVersionManager:
    """Monitors dataset lifecycle transitions, upgrades, and migration rollbacks."""

    def __init__(self, initial_version: str = "dataset_v1") -> None:
        self.current_version = initial_version
        self.version_history: List[str] = [initial_version]
        self.lifecycle_state = "STABLE"
        self._lock = threading.Lock()

    def get_status(self) -> Dict[str, Any]:
        """Returns details on the dataset state."""
        with self._lock:
            return {
                "current_version": self.current_version,
                "state": self.lifecycle_state,
                "history": list(self.version_history),
            }

    def transition_state(self, new_state: str) -> None:
        """Swaps active operational states."""
        with self._lock:
            self.lifecycle_state = new_state
            logger.info(f"Dataset lifecycle state transitioned to {new_state}")

    def trigger_migration(self, target_version: str) -> None:
        """Migrates dataset to a new target configuration version."""
        with self._lock:
            self.lifecycle_state = "MIGRATING"
            self.version_history.append(target_version)
            self.current_version = target_version
            self.lifecycle_state = "STABLE"
            logger.info(f"Dataset successfully migrated to version {target_version}")

    def trigger_rollback(self) -> str:
        """Rolls back the current dataset to the previous catalog snapshot version."""
        with self._lock:
            if len(self.version_history) <= 1:
                raise VersionMismatchException(
                    "No dataset version history available for rollback operation"
                )

            self.lifecycle_state = "ROLLBACK_IN_PROGRESS"
            self.version_history.pop()
            self.current_version = self.version_history[-1]
            self.lifecycle_state = "STABLE"
            logger.warning(f"Dataset rolled back to version {self.current_version}")
            return self.current_version


class KnowledgeRegistry:
    """Internal registry ledger mapping document metadata and active statuses."""

    def __init__(self) -> None:
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def register_document(
        self,
        doc_id: str,
        source_id: str,
        chunk_ids: List[str],
        metadata: Dict[str, Any],
    ) -> None:
        """Saves a document indexing registration record."""
        with self._lock:
            self._registry[doc_id] = {
                "document_id": doc_id,
                "source_id": source_id,
                "chunk_ids": list(chunk_ids),
                "metadata": dict(metadata),
                "status": "PUBLISHED",
            }
            logger.info(f"Registered document {doc_id} with {len(chunk_ids)} chunks")

    def update_status(self, doc_id: str, status: str) -> None:
        """Shifts document status (e.g. Published -> Archived)."""
        with self._lock:
            if doc_id in self._registry:
                self._registry[doc_id]["status"] = status
                logger.info(f"Updated status for document {doc_id} to {status}")

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves registered document metadata registry info."""
        with self._lock:
            return self._registry.get(doc_id)

    def remove_document(self, doc_id: str) -> None:
        """Removes a document catalog listing."""
        with self._lock:
            self._registry.pop(doc_id, None)
            logger.info(f"Removed document registry mapping for {doc_id}")

    def list_documents(self) -> List[str]:
        """Returns all registered document identifiers."""
        with self._lock:
            return list(self._registry.keys())
