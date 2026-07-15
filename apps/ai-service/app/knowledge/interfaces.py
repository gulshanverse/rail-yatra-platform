"""
Interface contracts for the Enterprise Knowledge & Embedding Platform.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple


class IKnowledgeSource(ABC):
    """Represents a data provider source."""

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Unique identifier of the source."""
        pass

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Static configurations of the source."""
        pass

    @abstractmethod
    async def fetch_payload(self) -> bytes:
        """Fetches raw document binary data from source."""
        pass


class IKnowledgeSourceRegistry(ABC):
    """Manages registered sources and their sync schedules."""

    @abstractmethod
    def register_source(self, source: IKnowledgeSource) -> None:
        """Registers a source connector."""
        pass

    @abstractmethod
    def deregister_source(self, source_id: str) -> None:
        """Removes a source connector."""
        pass

    @abstractmethod
    def get_source(self, source_id: str) -> IKnowledgeSource:
        """Retrieves a source connector by ID."""
        pass

    @abstractmethod
    def list_sources(self) -> List[str]:
        """Lists all registered source identifiers."""
        pass


class IDocumentIngestionPipeline(ABC):
    """Handles parsing, ingestion, transactional lifecycle status shifts, and rollback."""

    @abstractmethod
    async def ingest(
        self, doc_id: str, payload: bytes, source_id: str, metadata: Dict[str, Any]
    ) -> str:
        """Executes full document processing pipeline, chunking, and publishing."""
        pass

    @abstractmethod
    async def rollback_ingestion(self, doc_id: str) -> bool:
        """Removes all processed and indexed chunks if transactional error occurs."""
        pass


class IDocumentProcessor(ABC):
    """Pluggable component in the knowledge processing pipeline (e.g. Cleaning, PII redaction)."""

    @abstractmethod
    def process(
        self, content: bytes, metadata: Dict[str, Any]
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Processes content and enriches metadata block."""
        pass


class IChunkingStrategy(ABC):
    """Interface for pluggable text splitting algorithms."""

    @abstractmethod
    def split(self, text: str, doc_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Splits raw text content into standard chunks with metadata."""
        pass


class IEmbeddingProvider(ABC):
    """Unified interface wrapper for embedding models."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Target model identifier (e.g. bge-m3, text-embedding-3)."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Model output vector dimension."""
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Generates embedding representation for a search query string."""
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates batch embeddings for document chunks."""
        pass


class IVectorStore(ABC):
    """Vendor-independent vector database adapter layer."""

    @abstractmethod
    async def initialize_collection(self, collection_name: str, dimension: int) -> None:
        """Creates collection space with index configs if not exists."""
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> None:
        """Drops collection space."""
        pass

    @abstractmethod
    async def upsert_chunks(
        self,
        collection_name: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
    ) -> None:
        """Stores vectors paired with document metadata payloads."""
        pass

    @abstractmethod
    async def search_chunks(
        self,
        collection_name: str,
        query_vector: List[float],
        filter_metadata: Dict[str, Any],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Performs vector search under filtering conditions."""
        pass


class IRetrievalPolicy(ABC):
    """Retrieval routing strategy filter selector."""

    @abstractmethod
    def apply_policy(
        self, query: str, config: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Transforms query constraints and produces database query arguments."""
        pass


class IRetrievalCoordinator(ABC):
    """Coordinates hybrid lexical/semantic queries and enforces filters."""

    @abstractmethod
    async def retrieve(
        self, query: str, policy_name: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Executes retrieval pipelines according to active query strategies."""
        pass


class IContextAssembler(ABC):
    """Prepares retrieved chunks into prompt context budgets for the LLM."""

    @abstractmethod
    def assemble_context(
        self, query: str, chunks: List[Dict[str, Any]], token_limit: int
    ) -> str:
        """Performs deduplication, ranking, compression, and budget packing."""
        pass


# ======================================================================
# Phase 4.1 Planning Improvements Extension Interfaces
# ======================================================================


class IFreshnessEvaluator(ABC):
    """Interface for evaluating document freshness decay and scheduling refreshes."""

    @abstractmethod
    def evaluate_freshness(self, metadata: Dict[str, Any]) -> float:
        """Returns a normalized score (0.0 - 1.0) indicating freshness."""
        pass

    @abstractmethod
    def should_refresh(
        self, freshness_score: float, expiry_policy: Dict[str, Any]
    ) -> bool:
        """Returns True if the document has expired or needs updates."""
        pass


class ICitationGenerator(ABC):
    """Interface for generating source citations from retrieved chunks."""

    @abstractmethod
    def generate_citations(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Maps chunks back to their originating source documents."""
        pass


class IEmbeddingEvaluator(ABC):
    """Benchmarking suite for model adapters and embeddings comparisons."""

    @abstractmethod
    def evaluate_performance(
        self, provider: IEmbeddingProvider, golden_dataset: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculates benchmark metrics (Precision, Recall, MRR, nDCG, Latency, Cost)."""
        pass
