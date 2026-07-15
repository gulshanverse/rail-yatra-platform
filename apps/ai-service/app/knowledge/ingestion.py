"""
Document Ingestion Pipeline: Coordinates validation, cleaning, chunking, embedding, indexing, catalog registries, and rollback transaction controls.
"""

import logging
from typing import Dict, Any

from app.knowledge.interfaces import (
    IDocumentIngestionPipeline,
    IEmbeddingProvider,
    IVectorStore,
)
from app.knowledge.exceptions import (
    IngestionException,
    ProcessingException,
    ChunkingException,
    EmbeddingException,
    VectorStoreException,
)
from app.knowledge.processing import ProcessingPipeline
from app.knowledge.chunking import ChunkingEngine
from app.knowledge.registry import (
    KnowledgeRegistry,
    DatasetVersionManager,
    VersionManager,
)
from app.knowledge.vector_store import IndexManager
from app.knowledge.embedding import EmbeddingFactory
from app.knowledge.vector_store import VectorStoreFactory

logger = logging.getLogger("ai-service.knowledge.ingestion")


class DocumentIngestionPipeline(IDocumentIngestionPipeline):
    """Event-driven transaction coordinator managing document lifecycle scopes."""

    def __init__(
        self,
        embedding_provider: IEmbeddingProvider = None,
        vector_store: IVectorStore = None,
        registry: KnowledgeRegistry = None,
        index_mgr: IndexManager = None,
    ) -> None:
        self.embedding_provider = embedding_provider or EmbeddingFactory.get_provider()
        self.vector_store = vector_store or VectorStoreFactory.get_store()
        self.registry = registry or KnowledgeRegistry()
        self.index_mgr = index_mgr or IndexManager(self.vector_store)

        self.processor_pipeline = ProcessingPipeline()
        self.chunker = ChunkingEngine()
        self.dataset_mgr = DatasetVersionManager()
        self.version_mgr = VersionManager()

    async def ingest(
        self, doc_id: str, payload: bytes, source_id: str, metadata: Dict[str, Any]
    ) -> str:
        logger.info(
            f"Ingestion transaction started for document {doc_id} from source {source_id}"
        )

        # Build document catalog properties
        doc_metadata = dict(metadata)
        doc_metadata.update(
            {
                "document_id": doc_id,
                "source_id": source_id,
                "status": "VALIDATING",
                "version_matrix": self.version_mgr.get_version_matrix(),
            }
        )

        try:
            # 1. Processing pipeline stages: Clean, Redact PII, Validate, Score Quality
            logger.debug(
                f"Ingestion Stage 1: Running document processors for {doc_id}..."
            )
            processed_payload, processed_metadata = self.processor_pipeline.execute(
                payload, doc_metadata
            )

            # Transition status
            processed_metadata["status"] = "PROCESSING"

            # 2. Chunking strategy split executions
            logger.debug(f"Ingestion Stage 2: Chunking text content for {doc_id}...")
            text_content = processed_payload.decode("utf-8")
            chunks = self.chunker.execute_chunking(text_content, processed_metadata)

            if not chunks:
                raise IngestionException(
                    "Chunking stage failed: produced 0 chunks for indexing"
                )

            processed_metadata["status"] = "EMBEDDING"

            # 3. Batch embedding computations
            logger.debug(
                f"Ingestion Stage 3: Requesting embeddings for {len(chunks)} chunks..."
            )
            chunk_texts = [c["text"] for c in chunks]
            vectors = await self.embedding_provider.embed_documents(chunk_texts)

            processed_metadata["status"] = "INDEXED"

            # 4. Insert vectors and metadata payloads into the database
            logger.debug("Ingestion Stage 4: Indexing chunk vectors into collection...")
            payloads = [c["metadata"] for c in chunks]
            await self.index_mgr.initialize()
            await self.index_mgr.index_batch(vectors, payloads)

            # 5. Register in catalog registries and log state transitions
            chunk_ids = [c["chunk_id"] for c in chunks]
            self.registry.register_document(
                doc_id, source_id, chunk_ids, processed_metadata
            )

            logger.info(
                f"Ingestion transaction successfully published for document {doc_id}"
            )
            return "PUBLISHED"

        except (
            ProcessingException,
            ChunkingException,
            EmbeddingException,
            VectorStoreException,
            IngestionException,
        ) as ex:
            logger.error(
                f"Transaction failed during ingestion of {doc_id}: {ex}. Initiating rollback..."
            )
            await self.rollback_ingestion(doc_id)
            raise IngestionException(
                f"Ingestion pipeline failed and has been rolled back: {ex}"
            )
        except Exception as e:
            logger.critical(
                f"Unexpected crash in ingestion pipeline for {doc_id}: {e}. Initiating rollback..."
            )
            await self.rollback_ingestion(doc_id)
            raise IngestionException(f"Pipeline crashed and has been rolled back: {e}")

    async def rollback_ingestion(self, doc_id: str) -> bool:
        """Removes indexing collection segments and removes document mapping entries (Atomicity)."""
        logger.warning(f"Executing rollback transactions for document {doc_id}")

        try:
            # 1. Clean collection segments
            await self.index_mgr.remove_document_chunks(doc_id)

            # 2. De-register catalog index mapping entries
            self.registry.remove_document(doc_id)

            logger.info(f"Rollback completed successfully for document {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error during rollback pipeline execution: {e}")
            return False

    def get_registered_documents_count(self) -> int:
        """Helper returns catalog counter."""
        return len(self.registry.list_documents())
