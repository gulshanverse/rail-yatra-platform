"""
Entry point for the Enterprise Knowledge & Embedding Platform.
Exposes interfaces, pipelines, and registries.
"""

from app.knowledge.interfaces import (
    IKnowledgeSource,
    IKnowledgeSourceRegistry,
    IDocumentIngestionPipeline,
    IDocumentProcessor,
    IChunkingStrategy,
    IEmbeddingProvider,
    IVectorStore,
    IRetrievalPolicy,
    IRetrievalCoordinator,
    IContextAssembler,
    IFreshnessEvaluator,
    ICitationGenerator,
    IEmbeddingEvaluator,
    IIntentClassifier,
    IQueryDecomposer,
    ICrossEncoderReranker,
    ISemanticCache,
    ICollectionManager,
)
from app.knowledge.exceptions import (
    KnowledgeException,
    KnowledgeSourceException,
    IngestionException,
    ProcessingException,
    ChunkingException,
    EmbeddingException,
    VectorStoreException,
    VersionMismatchException,
    RetrievalException,
)
from app.knowledge.config import knowledge_settings
from app.knowledge.registry import (
    KnowledgeSourceRegistry,
    VersionManager,
    DatasetVersionManager,
    KnowledgeRegistry,
)
from app.knowledge.processing import (
    TextCleanerProcessor,
    PIIRedactorProcessor,
    LanguageDetectorProcessor,
    ContentValidatorProcessor,
    QualityScorerProcessor,
    ProcessingPipeline,
)
from app.knowledge.chunking import (
    FixedSizeChunkingStrategy,
    HeadingAwareChunkingStrategy,
    SemanticSentenceChunkingStrategy,
    HierarchicalChunkingStrategy,
    ChunkingEngine,
)
from app.knowledge.embedding import (
    MockEmbeddingProvider,
    OpenAIEmbeddingProvider,
    GeminiEmbeddingProvider,
    EmbeddingFactory,
    EmbeddingEvaluator,
)
from app.knowledge.vector_store import (
    MockVectorStore,
    VectorStoreFactory,
    IndexManager,
)
from app.knowledge.retrieval import (
    RetrievalPolicy,
    RetrievalCoordinator,
    QueryProcessor,
    IntentClassifier,
    QueryDecomposer,
    CrossEncoderReranker,
)
from app.knowledge.assembly import (
    ContextAssembler,
)
from app.knowledge.ingestion import (
    DocumentIngestionPipeline,
)
from app.knowledge.cache import (
    SemanticCache,
)
from app.knowledge.collection import (
    CollectionManager,
)


__all__ = [
    # Interfaces
    "IKnowledgeSource",
    "IKnowledgeSourceRegistry",
    "IDocumentIngestionPipeline",
    "IDocumentProcessor",
    "IChunkingStrategy",
    "IEmbeddingProvider",
    "IVectorStore",
    "IRetrievalPolicy",
    "IRetrievalCoordinator",
    "IContextAssembler",
    "IFreshnessEvaluator",
    "ICitationGenerator",
    "IEmbeddingEvaluator",
    # Exceptions
    "KnowledgeException",
    "KnowledgeSourceException",
    "IngestionException",
    "ProcessingException",
    "ChunkingException",
    "EmbeddingException",
    "VectorStoreException",
    "VersionMismatchException",
    "RetrievalException",
    # Configurations
    "knowledge_settings",
    # Registries and Managers
    "KnowledgeSourceRegistry",
    "VersionManager",
    "DatasetVersionManager",
    "KnowledgeRegistry",
    # Processing
    "TextCleanerProcessor",
    "PIIRedactorProcessor",
    "LanguageDetectorProcessor",
    "ContentValidatorProcessor",
    "QualityScorerProcessor",
    "ProcessingPipeline",
    # Chunking
    "FixedSizeChunkingStrategy",
    "HeadingAwareChunkingStrategy",
    "SemanticSentenceChunkingStrategy",
    "HierarchicalChunkingStrategy",
    "ChunkingEngine",
    # Embedding
    "MockEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "GeminiEmbeddingProvider",
    "EmbeddingFactory",
    "EmbeddingEvaluator",
    # Vector store
    "MockVectorStore",
    "VectorStoreFactory",
    "IndexManager",
    # Retrieval
    "RetrievalPolicy",
    "RetrievalCoordinator",
    "QueryProcessor",
    "IntentClassifier",
    "QueryDecomposer",
    "CrossEncoderReranker",
    # Context Assembly
    "ContextAssembler",
    # Ingestion orchestrator
    "DocumentIngestionPipeline",
    # Cache and Collection Manager
    "SemanticCache",
    "CollectionManager",
    # Interfaces
    "IIntentClassifier",
    "IQueryDecomposer",
    "ICrossEncoderReranker",
    "ISemanticCache",
    "ICollectionManager",
]
