"""
FastAPI Dependency Providers – Centralized DI container for service injection.

Design:
  - Each ``get_*`` function is intended for use with ``FastAPI.Depends()``.
  - Services are NOT instantiated yet (Tickets 3+).
  - Placeholder functions raise ``NotImplementedError`` with clear messages
    so that accidentally calling an unimplemented dependency fails loudly.
  - ``get_request_id`` generates and binds a UUID to the request context
    for structured logging traceability.

Usage in routes:
    from app.core.dependencies import get_chat_service
    @router.post("/chat")
    async def chat(service = Depends(get_chat_service)):
        ...
"""

import uuid
from typing import Any

from app.core.logger import get_logger, request_id_ctx, session_id_ctx

logger = get_logger(__name__)

# ── Singleton caches ──────────────────────────────
_embedding_provider: Any = None
_vector_store: Any = None
_retrieval_service: Any = None
_memory_service: Any = None
_llm_provider: Any = None
_rag_orchestrator: Any = None
_chat_service: Any = None
_ingestion_service: Any = None


# ── Request Context ───────────────────────────────
async def get_request_id() -> str:
    """Generate a unique request ID and bind it to the logging context.

    Returns:
        A UUID4 string identifying this request across all log lines.
    """
    rid = str(uuid.uuid4())
    request_id_ctx.set(rid)
    return rid


async def bind_session_id(session_id: str) -> str:
    """Bind a session ID to the logging context for the current request.

    Args:
        session_id: The chat session UUID from the request body.

    Returns:
        The same session_id, now bound to contextvars.
    """
    session_id_ctx.set(session_id)
    return session_id


# ── Service Stubs (Ticket 3+) ────────────────────
def get_embedding_provider() -> Any:
    """Provide the SentenceTransformer embedding provider (singleton).

    Returns:
        SentenceTransformerEmbeddingProvider instance.

    Note:
        The provider is created once and cached for the lifetime of the
        application.  The underlying SentenceTransformer model is loaded
        lazily on first use.
    """
    global _embedding_provider
    if _embedding_provider is None:
        from app.embeddings.sentence_transformer import (
            SentenceTransformerEmbeddingProvider,
        )

        _embedding_provider = SentenceTransformerEmbeddingProvider()
        logger.info("EmbeddingProvider singleton created")
    return _embedding_provider


def get_vector_store() -> Any:
    """Provide the ChromaDB vector store (singleton).

    Returns:
        ChromaVectorStore instance.

    Note:
        The store is created once and cached for the lifetime of the
        application.  ChromaDB collections persist to disk automatically.
    """
    global _vector_store
    if _vector_store is None:
        from app.vectorstore.chroma_store import ChromaVectorStore

        _vector_store = ChromaVectorStore()
        logger.info("VectorStore singleton created")
    return _vector_store


def get_retrieval_service() -> Any:
    """Provide the RetrievalService (singleton).

    Returns:
        RetrievalService instance wired to the existing EmbeddingProvider
        and VectorStore singletons.

    Note:
        The service is created once and cached for the lifetime of the
        application.  It reuses the existing singletons for embedding
        and vector store.
    """
    global _retrieval_service
    if _retrieval_service is None:
        from app.services.retrieval_service import RetrievalService

        embedding_provider = get_embedding_provider()
        vector_store = get_vector_store()
        _retrieval_service = RetrievalService(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )
        logger.info("RetrievalService singleton created")
    return _retrieval_service


def get_memory_service() -> Any:
    """Provide the in-memory conversation history manager (singleton).

    Returns:
        MemoryService instance wired to the configured message limit.

    Note:
        The service is created once and cached for the lifetime of the
        application.  Conversation data lives in-process only and is lost
        on restart.
    """
    global _memory_service
    if _memory_service is None:
        from app.services.memory_service import MemoryService

        _memory_service = MemoryService()
        logger.info("MemoryService singleton created")
    return _memory_service


def get_llm_service() -> Any:
    """Provide the LLM provider (singleton).

    Selects the provider based on the ``LLM_PROVIDER`` setting:
      - ``"openrouter"`` → ``OpenRouterProvider``
      - ``"gemini"``     → ``GeminiProvider``

    Returns:
        An ``LLMProvider`` instance wired to the configured API key and model.

    Note:
        The provider is created once and cached for the lifetime of the
        application.  The underlying client is initialised lazily on first use.
    """
    global _llm_provider
    if _llm_provider is None:
        from app.core.config import settings

        provider_name = settings.LLM_PROVIDER.lower()

        if provider_name == "openrouter":
            from app.llm.openrouter_provider import OpenRouterProvider

            _llm_provider = OpenRouterProvider()
            logger.info(
                "LLMProvider singleton created",
                extra={"provider": "openrouter"},
            )
        elif provider_name == "gemini":
            from app.llm.gemini_provider import GeminiProvider

            _llm_provider = GeminiProvider()
            logger.info(
                "LLMProvider singleton created",
                extra={"provider": "gemini"},
            )
        else:
            raise ValueError(
                f"Unknown LLM_PROVIDER: '{provider_name}'. "
                "Must be 'openrouter' or 'gemini'."
            )
    return _llm_provider


def get_rag_orchestrator() -> Any:
    """Provide the RAG Orchestrator (singleton).

    Returns:
        RAGOrchestrator instance wired to all required services.

    Note:
        The orchestrator is created once and cached for the lifetime of
        the application.
    """
    global _rag_orchestrator
    if _rag_orchestrator is None:
        from app.services.rag_orchestrator import RAGOrchestrator

        retrieval_service = get_retrieval_service()
        memory_service = get_memory_service()
        llm_provider = get_llm_service()
        _rag_orchestrator = RAGOrchestrator(
            retrieval_service=retrieval_service,
            memory_service=memory_service,
            llm_provider=llm_provider,
        )
        logger.info("RAGOrchestrator singleton created")
    return _rag_orchestrator


def get_chat_service() -> Any:
    """Provide the Chat Service (singleton).

    This is the top-level business layer dependency that wraps the
    RAG Orchestrator and exposes the public chat API.

    Returns:
        ChatService instance wired to the RAGOrchestrator.

    Note:
        The service is created once and cached for the lifetime of
        the application.
    """
    global _chat_service
    if _chat_service is None:
        from app.services.chat_service import ChatService

        orchestrator = get_rag_orchestrator()
        _chat_service = ChatService(orchestrator=orchestrator)
        logger.info("ChatService singleton created")
    return _chat_service


def get_ingestion_service() -> Any:
    """Provide the IngestionService (singleton).

    Returns:
        IngestionService instance wired to the existing DocumentLoader,
        TextChunker, EmbeddingProvider, and VectorStore singletons.

    Note:
        The service is created once and cached for the lifetime of the
        application.  It reuses existing singletons for embedding and
        vector store.
    """
    global _ingestion_service
    if _ingestion_service is None:
        from app.services.document_loader import DocumentLoader
        from app.services.ingestion_service import IngestionService
        from app.services.text_chunker import TextChunker

        embedding_provider = get_embedding_provider()
        vector_store = get_vector_store()
        _ingestion_service = IngestionService(
            document_loader=DocumentLoader(),
            text_chunker=TextChunker(),
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )
        logger.info("IngestionService singleton created")
    return _ingestion_service


# ── Singleton Reset ─────────────────────────────
def reset_singletons() -> None:
    """Reset all singleton caches to ``None``.

    This is the **only** function permitted to clear the DI container's
    singleton instances.  It is called during shutdown to ensure no stale
    references persist across restarts.

    Note:
        This function clears references only; it does not call cleanup
        methods on individual services.  Services that require explicit
        teardown should be handled by the lifecycle layer before calling
        this function.
    """
    global _embedding_provider, _vector_store, _retrieval_service
    global _memory_service, _llm_provider, _rag_orchestrator, _chat_service
    global _ingestion_service

    _embedding_provider = None
    _vector_store = None
    _retrieval_service = None
    _memory_service = None
    _llm_provider = None
    _rag_orchestrator = None
    _chat_service = None
    _ingestion_service = None

    logger.info("Singleton caches reset")
