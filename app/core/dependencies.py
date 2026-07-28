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

from fastapi import Request

from app.core.logger import request_id_ctx, session_id_ctx, get_logger

logger = get_logger(__name__)

# ── Singleton caches ──────────────────────────────
_embedding_provider: Any = None
_vector_store: Any = None
_retrieval_service: Any = None


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
    """Provide the in-memory conversation history manager.

    Returns:
        MemoryService instance (not yet implemented).

    Raises:
        NotImplementedError: Until Ticket 4 implements MemoryService.
    """
    raise NotImplementedError(
        "MemoryService is not yet implemented. See Ticket 4."
    )


def get_llm_service() -> Any:
    """Provide the Google Gemini LLM client.

    Returns:
        GeminiService instance (not yet implemented).

    Raises:
        NotImplementedError: Until Ticket 5 implements GeminiService.
    """
    raise NotImplementedError(
        "GeminiService is not yet implemented. See Ticket 5."
    )


def get_chat_service() -> Any:
    """Provide the orchestrating ChatService.

    This is the top-level dependency that composes MemoryService,
    EmbeddingService, VectorStore, and GeminiService.

    Returns:
        ChatService instance (not yet implemented).

    Raises:
        NotImplementedError: Until Ticket 6 implements ChatService.
    """
    raise NotImplementedError(
        "ChatService is not yet implemented. See Ticket 6."
    )
