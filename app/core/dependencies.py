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

# ── Singleton cache for embedding provider ────────
_embedding_provider: Any = None


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
    """Provide the ChromaDB vector store client.

    Returns:
        VectorStore instance (not yet implemented).

    Raises:
        NotImplementedError: Until Ticket 3 implements VectorStore.
    """
    raise NotImplementedError(
        "VectorStore is not yet implemented. See Ticket 3."
    )


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
