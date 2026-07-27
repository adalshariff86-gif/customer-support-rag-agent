"""
Abstract Vector Store – Clean Architecture interface.

All vector store implementations must inherit from ``VectorStore`` and
implement the required methods. Business logic should depend only on
this interface so that backends can be swapped without code changes.

Usage:
    from app.vectorstore.base import VectorStore, RetrievedChunk

    class MyStore(VectorStore):
        ...
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """A single chunk returned from a similarity search.

    Attributes:
        chunk_id:    Unique identifier of the stored chunk.
        text:        Original text content of the chunk.
        metadata:    Arbitrary key-value metadata associated with the chunk.
        score:       Normalised similarity score (0.0 – 1.0, higher = more similar).
        distance:    Raw distance value returned by the vector backend.
    """

    chunk_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    distance: float = 0.0


class VectorStore(ABC):
    """Abstract base class for all vector store backends.

    Every concrete backend (ChromaDB, Pinecone, Qdrant, etc.) must
    implement these methods. Business logic should depend only on
    this interface so that backends can be swapped without code changes.
    """

    # ── Collection Management ───────────────────────

    @abstractmethod
    def create_collection(self, collection_name: str) -> None:
        """Create a new collection.

        Must be idempotent — calling twice with the same name must not fail.

        Args:
            collection_name: Unique name for the collection.

        Raises:
            VectorStoreException: If creation fails unexpectedly.
        """

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection.

        Must be idempotent — deleting a non-existent collection must not fail.

        Args:
            collection_name: Name of the collection to delete.

        Raises:
            VectorStoreException: If deletion fails unexpectedly.
        """

    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """Check whether a collection exists.

        Args:
            collection_name: Name of the collection to check.

        Returns:
            ``True`` if the collection exists, ``False`` otherwise.

        Raises:
            VectorStoreException: If the check fails.
        """

    @abstractmethod
    def count(self, collection_name: str) -> int:
        """Return the number of documents in a collection.

        Args:
            collection_name: Name of the collection.

        Returns:
            Number of documents stored.

        Raises:
            VectorStoreException: If the count operation fails.
        """

    @abstractmethod
    def reset(self) -> None:
        """Delete all collections and reset the store to an empty state.

        Must be idempotent.

        Raises:
            VectorStoreException: If the reset operation fails.
        """

    # ── Document Operations ────────────────────────

    @abstractmethod
    def add_documents(
        self,
        collection_name: str,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Insert documents with pre-computed embeddings into a collection.

        All input lists must have the same length.

        Args:
            collection_name: Target collection.
            ids:             Unique document identifiers.
            texts:           Original text content for each document.
            embeddings:      Pre-computed embedding vectors.
            metadatas:       Metadata dictionaries for each document.

        Raises:
            ValidationException: If input lists have mismatched lengths or
                                 contain invalid data.
            VectorStoreException: If the insertion fails.
        """

    @abstractmethod
    def delete_documents(self, collection_name: str, ids: list[str]) -> None:
        """Remove documents by their IDs.

        Must be tolerant of IDs that do not exist in the collection.

        Args:
            collection_name: Target collection.
            ids:             Document identifiers to remove.

        Raises:
            VectorStoreException: If the deletion fails.
        """

    @abstractmethod
    def update_documents(
        self,
        collection_name: str,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Update existing documents by their IDs.

        All input lists must have the same length.  Only documents whose
        IDs already exist in the collection are modified; behaviour for
        missing IDs is undefined and implementation-dependent.

        Args:
            collection_name: Target collection.
            ids:             Document identifiers to update.
            texts:           Replacement text content for each document.
            embeddings:      Replacement embedding vectors.
            metadatas:       Replacement metadata dictionaries.

        Raises:
            ValidationException: If input lists have mismatched lengths or
                                 contain invalid data.
            VectorStoreException: If the update fails.
        """

    @abstractmethod
    def get_collection_stats(self, collection_name: str) -> dict[str, Any]:
        """Return statistics for a collection.

        Args:
            collection_name: Name of the collection.

        Returns:
            A dictionary containing at least: ``name``, ``count``,
            and any available metadata such as embedding dimension
            or persistence path.

        Raises:
            VectorStoreException: If the stats operation fails.
        """

    @abstractmethod
    def clear_collection(self, collection_name: str) -> None:
        """Remove all documents from a collection.

        The collection itself is preserved and remains usable.

        Must be idempotent — clearing an empty collection must not fail.

        Args:
            collection_name: Name of the collection to clear.

        Raises:
            VectorStoreException: If the clear operation fails.
        """

    # ── Search ─────────────────────────────────────

    @abstractmethod
    def similarity_search(
        self,
        collection_name: str,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Find the most similar documents to a query embedding.

        Results are returned in descending order of similarity.

        Args:
            collection_name: Target collection.
            query_embedding: Pre-computed query vector.
            top_k:           Maximum number of results to return.

        Returns:
            A list of ``RetrievedChunk`` objects, ordered by relevance.

        Raises:
            ValidationException: If ``query_embedding`` is empty or
                                 ``top_k`` is not positive.
            VectorStoreException: If the search fails.
        """
