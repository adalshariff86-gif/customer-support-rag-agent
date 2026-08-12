"""
Retrieval Service – RAG Retrieval Layer.

Retrieves the most relevant document chunks from the Vector Store and
prepares clean context for the LLM.  Follows Clean Architecture by
depending only on the ``EmbeddingProvider`` and ``VectorStore`` interfaces.

Responsibilities:
  - Validate user queries
  - Generate query embeddings via the injected ``EmbeddingProvider``
  - Perform similarity search via the injected ``VectorStore``
  - Filter invalid or empty chunks
  - Build a formatted context string for the LLM
  - Return a structured ``RetrievedContext`` result

Usage:
    from app.services.retrieval_service import RetrievalService
    from app.embeddings.base import EmbeddingProvider
    from app.vectorstore.base import VectorStore

    service = RetrievalService(
        embedding_provider=my_provider,
        vector_store=my_store,
    )
    result = service.retrieve(query="How do I reset my password?")
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.core.exceptions import (
    EmbeddingException,
    RetrievalException,
    ValidationException,
)
from app.core.logger import get_logger
from app.embeddings.base import EmbeddingProvider
from app.vectorstore.base import RetrievedChunk, VectorStore

logger = get_logger(__name__)

# ── Constants ────────────────────────────────────
_DEFAULT_COLLECTION = "documents"
_SEPARATOR = "\n------------------------------------\n"


@dataclass(frozen=True, slots=True)
class RetrievedDocument:
    """A single retrieved document returned to callers.

    Attributes:
        id:        Unique document identifier.
        content:   Relevant text excerpt.
        score:     Normalised similarity score (0.0 – 1.0).
        metadata:  Arbitrary key-value metadata.
    """

    id: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RetrievedContext:
    """Structured result from a retrieval operation.

    Attributes:
        documents:       List of retrieved documents in relevance order.
        context:         Formatted context string ready for the LLM.
        document_count:  Number of documents included in the context.
        query:           Original user query.
        elapsed_ms:      Total retrieval time in milliseconds.
    """

    documents: list[RetrievedDocument]
    context: str
    query: str
    elapsed_ms: float

    @property
    def document_count(self) -> int:
        """Return the number of documents (computed, never stale)."""
        return len(self.documents)


class RetrievalService:
    """RAG retrieval service.

    Orchestrates embedding generation, similarity search, filtering,
    and context formatting.  Does NOT call the LLM or manage memory.

    Args:
        embedding_provider:  Injected ``EmbeddingProvider`` instance.
        vector_store:        Injected ``VectorStore`` instance.
        collection_name:     Target collection name (default ``"documents"``).
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        collection_name: str = _DEFAULT_COLLECTION,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._collection_name = collection_name

    # ── Public API ─────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        collection_name: str | None = None,
    ) -> RetrievedContext:
        """Retrieve relevant documents for a user query.

        Args:
            query:            The user's search query.
            top_k:            Maximum number of results to return.
            collection_name:  Override for the collection to search.

        Returns:
            A ``RetrievedContext`` containing formatted context and
            structured document metadata.

        Raises:
            ValidationException:  If the query is empty, whitespace-only,
                                  or ``top_k`` is not positive.
            RetrievalException:   If any unexpected error occurs during
                                  embedding, search, filtering, or
                                  context building.
        """
        start = time.perf_counter()

        try:
            # ── 1. Validate input ──────────────────
            self._validate_query(query, top_k)
            logger.info(
                "Retrieval started",
                extra={
                    "query_length": len(query),
                    "query_preview": query[:50],
                    "top_k": top_k,
                },
            )

            # ── 2. Generate query embedding ────────
            embedding = self._create_embedding(query)
            logger.info(
                "Query embedding created",
                extra={"dimension": len(embedding)},
            )

            # ── 3. Similarity search ───────────────
            target_collection = collection_name or self._collection_name
            logger.info(
                "Similarity search started",
                extra={"collection": target_collection, "top_k": top_k},
            )
            raw_chunks = self._vector_store.similarity_search(
                collection_name=target_collection,
                query_embedding=embedding,
                top_k=top_k,
            )
            logger.info(
                "Similarity search completed",
                extra={"raw_count": len(raw_chunks)},
            )

            # ── 4. Filter invalid results ──────────
            filtered_chunks = self._filter_chunks(raw_chunks)
            logger.info(
                "Filtering complete",
                extra={
                    "raw_count": len(raw_chunks),
                    "filtered_count": len(filtered_chunks),
                },
            )

            # ── 5. Build context ───────────────────
            documents = [self._chunk_to_document(c) for c in filtered_chunks]
            context = self._build_context(documents)
            logger.info("Context built", extra={"document_count": len(documents)})

            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "Retrieval completed",
                extra={"elapsed_ms": elapsed_ms, "document_count": len(documents)},
            )

            return RetrievedContext(
                documents=documents,
                context=context,
                query=query,
                elapsed_ms=elapsed_ms,
            )

        except (ValidationException, EmbeddingException):
            raise
        except RetrievalException:
            raise
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "Retrieval failed",
                extra={"error": str(exc), "elapsed_ms": elapsed_ms},
            )
            raise RetrievalException(
                message="An unexpected error occurred during retrieval.",
                details={"error": str(exc), "query": query, "top_k": top_k},
            ) from exc

    # ── Private helpers ────────────────────────────

    def _validate_query(self, query: str, top_k: int) -> None:
        """Validate the user query and top_k parameter.

        Raises:
            ValidationException: If validation fails.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValidationException(
                message="Query must not be empty or whitespace-only.",
                details={"field": "query", "value": repr(query)},
            )

        if not isinstance(top_k, int) or top_k <= 0:
            raise ValidationException(
                message="top_k must be a positive integer.",
                details={"field": "top_k", "value": top_k},
            )

    def _create_embedding(self, query: str) -> list[float]:
        """Generate an embedding vector for the query.

        Raises:
            ValidationException: If the embedding provider rejects the input.
            EmbeddingException:  If the embedding provider fails internally.
            RetrievalException:  If an unexpected error occurs.
        """
        try:
            return self._embedding_provider.embed_query(query)
        except (ValidationException, EmbeddingException):
            raise
        except Exception as exc:
            raise RetrievalException(
                message="Failed to create query embedding.",
                details={"error": str(exc), "query_length": len(query)},
            ) from exc

    def _filter_chunks(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Discard empty, blank, duplicate, or invalid chunks while preserving order.

        Filtering rules:
          - Discard chunks with empty or blank ``text``.
          - Discard chunks with invalid ``metadata`` (must be a dict).
          - Discard chunks with empty ``chunk_id``.
          - Deduplicate by ``chunk_id`` (keep first occurrence).
          - Preserve the original ordering from the similarity search.

        Returns:
            A filtered, deduplicated list of ``RetrievedChunk`` objects.
        """
        filtered: list[RetrievedChunk] = []
        seen_ids: set[str] = set()

        for chunk in chunks:
            # Discard empty text
            if not chunk.text or not chunk.text.strip():
                continue

            # Discard invalid metadata
            if not isinstance(chunk.metadata, dict):
                continue

            # Discard empty chunk_id
            if not chunk.chunk_id or not str(chunk.chunk_id).strip():
                continue

            # Deduplicate by chunk_id
            if chunk.chunk_id in seen_ids:
                continue
            seen_ids.add(chunk.chunk_id)

            filtered.append(chunk)

        return filtered

    def _chunk_to_document(self, chunk: RetrievedChunk) -> RetrievedDocument:
        """Convert a ``RetrievedChunk`` to a ``RetrievedDocument``.

        Args:
            chunk: The raw chunk from the vector store.

        Returns:
            A ``RetrievedDocument`` ready for external consumption.
        """
        return RetrievedDocument(
            id=chunk.chunk_id,
            content=chunk.text.strip(),
            score=chunk.score,
            metadata=chunk.metadata,
        )

    def _build_context(self, documents: list[RetrievedDocument]) -> str:
        """Build a formatted context string from retrieved documents.

        Format:
            Document: <source>
            <content>
            ------------------------------------
            Document: <source>
            <content>

        Args:
            documents: List of retrieved documents.

        Returns:
            A single formatted context string.
        """
        if not documents:
            return ""

        parts: list[str] = []
        for doc in documents:
            source_label = doc.metadata.get("source", doc.id)
            section = f"Document: {source_label}"
            parts.append(f"{section}\n{doc.content}")

        return _SEPARATOR.join(parts)
