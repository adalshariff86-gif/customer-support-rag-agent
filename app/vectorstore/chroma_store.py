"""
ChromaDB Vector Store – Persistent vector storage using ChromaDB.

Implements the ``VectorStore`` ABC with a ChromaDB ``PersistentClient``.
Collections survive application restarts via on-disk persistence.

Usage:
    from app.vectorstore.chroma_store import ChromaVectorStore

    store = ChromaVectorStore(persist_directory="./data/chroma")
    store.create_collection("documents")
    store.add_documents(
        collection_name="documents",
        ids=["chunk_1"],
        texts=["Hello world"],
        embeddings=[[0.1, 0.2, ...]],
        metadatas=[{"source": "faq.md"}],
    )
    results = store.similarity_search("documents", query_embedding=[0.1, ...], top_k=5)
"""

from __future__ import annotations

import time
from threading import Lock
from typing import Any

from app.core.config import settings
from app.core.exceptions import ValidationException, VectorStoreException
from app.core.logger import get_logger
from app.vectorstore.base import RetrievedChunk, VectorStore

logger = get_logger(__name__)

_CHROMA_DISTANCE_CUTOFF = 2.0


class ChromaVectorStore(VectorStore):
    """ChromaDB-backed persistent vector store.

    Attributes:
        persist_directory: Filesystem path for ChromaDB persistence.
    """

    _client: Any = None
    _client_lock: Lock = Lock()

    def __init__(self, persist_directory: str | None = None) -> None:
        """Initialise the store with an optional persistence directory.

        Args:
            persist_directory: Directory for ChromaDB data files.
                               Defaults to ``settings.CHROMA_PERSIST_DIRECTORY``.
        """
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIRECTORY

    # ── Client lifecycle ───────────────────────────

    def _get_client(self) -> Any:
        """Return the shared ChromaDB ``PersistentClient`` (lazy, thread-safe)."""
        if ChromaVectorStore._client is not None:
            return ChromaVectorStore._client

        with ChromaVectorStore._client_lock:
            if ChromaVectorStore._client is not None:
                return ChromaVectorStore._client

            try:
                import chromadb

                logger.info(
                    "Initialising ChromaDB PersistentClient",
                    extra={"persist_directory": self.persist_directory},
                )
                ChromaVectorStore._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                )
                logger.info("ChromaDB PersistentClient initialised")
            except Exception as exc:
                logger.error(
                    "Failed to initialise ChromaDB client",
                    extra={"persist_directory": self.persist_directory, "error": str(exc)},
                )
                raise VectorStoreException(
                    message="Failed to initialise ChromaDB client.",
                    details={"persist_directory": self.persist_directory, "error": str(exc)},
                ) from exc

        return ChromaVectorStore._client

    def _get_collection(self, collection_name: str) -> Any:
        """Return a ChromaDB collection handle by name.

        Args:
            collection_name: Name of the collection.

        Raises:
            VectorStoreException: If the collection cannot be retrieved.
        """
        try:
            client = self._get_client()
            return client.get_collection(name=collection_name)
        except Exception as exc:
            raise VectorStoreException(
                message=f"Failed to get collection '{collection_name}'.",
                details={"collection_name": collection_name, "error": str(exc)},
            ) from exc

    # ── Collection Management ───────────────────────

    def create_collection(self, collection_name: str) -> None:
        """Create a collection (idempotent).

        Args:
            collection_name: Unique name for the collection.

        Raises:
            VectorStoreException: If creation fails unexpectedly.
        """
        try:
            client = self._get_client()
            client.get_or_create_collection(name=collection_name)
            logger.info("Collection created / ensured", extra={"collection_name": collection_name})
        except VectorStoreException:
            raise
        except Exception as exc:
            logger.error(
                "Failed to create collection",
                extra={"collection_name": collection_name, "error": str(exc)},
            )
            raise VectorStoreException(
                message=f"Failed to create collection '{collection_name}'.",
                details={"collection_name": collection_name, "error": str(exc)},
            ) from exc

    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection (idempotent).

        Args:
            collection_name: Name of the collection to delete.

        Raises:
            VectorStoreException: If deletion fails unexpectedly.
        """
        try:
            client = self._get_client()
            try:
                client.delete_collection(name=collection_name)
                logger.info("Collection deleted", extra={"collection_name": collection_name})
            except Exception as not_found_exc:
                if "does not exist" in str(not_found_exc).lower() or type(not_found_exc).__name__ == "NotFoundError":
                    logger.info(
                        "Collection already absent — delete is no-op",
                        extra={"collection_name": collection_name},
                    )
                else:
                    raise
        except VectorStoreException:
            raise
        except Exception as exc:
            logger.error(
                "Failed to delete collection",
                extra={"collection_name": collection_name, "error": str(exc)},
            )
            raise VectorStoreException(
                message=f"Failed to delete collection '{collection_name}'.",
                details={"collection_name": collection_name, "error": str(exc)},
            ) from exc

    def collection_exists(self, collection_name: str) -> bool:
        """Check whether a collection exists.

        Args:
            collection_name: Name of the collection to check.

        Returns:
            ``True`` if the collection exists.

        Raises:
            VectorStoreException: If the check fails.
        """
        try:
            client = self._get_client()
            collections = client.list_collections()
            return any(
                getattr(c, "name", c) == collection_name for c in collections
            )
        except VectorStoreException:
            raise
        except Exception as exc:
            raise VectorStoreException(
                message=f"Failed to check collection existence '{collection_name}'.",
                details={"collection_name": collection_name, "error": str(exc)},
            ) from exc

    def count(self, collection_name: str) -> int:
        """Return the number of documents in a collection.

        Args:
            collection_name: Name of the collection.

        Returns:
            Number of documents stored.

        Raises:
            VectorStoreException: If the count operation fails.
        """
        try:
            collection = self._get_collection(collection_name)
            result = collection.count()
            logger.debug(
                "Collection count",
                extra={"collection_name": collection_name, "count": result},
            )
            return result
        except VectorStoreException:
            raise
        except Exception as exc:
            raise VectorStoreException(
                message=f"Failed to count documents in '{collection_name}'.",
                details={"collection_name": collection_name, "error": str(exc)},
            ) from exc

    def reset(self) -> None:
        """Delete all collections and reset the store (idempotent).

        Raises:
            VectorStoreException: If the reset fails.
        """
        try:
            client = self._get_client()
            collections = client.list_collections()
            for coll in collections:
                name = getattr(coll, "name", coll)
                try:
                    client.delete_collection(name=name)
                except Exception:
                    pass
            logger.info("Vector store reset", extra={"deleted_collections": len(collections)})
        except VectorStoreException:
            raise
        except Exception as exc:
            logger.error("Failed to reset vector store", extra={"error": str(exc)})
            raise VectorStoreException(
                message="Failed to reset vector store.",
                details={"error": str(exc)},
            ) from exc

    def get_collection_stats(self, collection_name: str) -> dict[str, Any]:
        """Return statistics for a collection.

        Args:
            collection_name: Name of the collection.

        Returns:
            A dictionary with ``name``, ``count``, ``persist_directory``,
            and any available metadata.

        Raises:
            VectorStoreException: If the stats operation fails.
        """
        try:
            collection = self._get_collection(collection_name)
            doc_count = collection.count()

            embedding_dim: int | None = None
            try:
                peek = collection.peek(limit=1)
                sample_embeddings = peek.get("embeddings", [])
                if sample_embeddings:
                    embedding_dim = len(sample_embeddings[0])
            except Exception:
                pass

            stats: dict[str, Any] = {
                "name": collection_name,
                "count": doc_count,
                "persist_directory": self.persist_directory,
                "embedding_dimension": embedding_dim,
            }

            logger.info(
                "Collection stats retrieved",
                extra={"collection_name": collection_name, "count": doc_count},
            )
            return stats
        except VectorStoreException:
            raise
        except Exception as exc:
            logger.error(
                "Failed to retrieve collection stats",
                extra={"collection_name": collection_name, "error": str(exc)},
            )
            raise VectorStoreException(
                message=f"Failed to retrieve stats for '{collection_name}'.",
                details={"collection_name": collection_name, "error": str(exc)},
            ) from exc

    def clear_collection(self, collection_name: str) -> None:
        """Remove all documents from a collection.

        The collection itself is preserved and remains usable.

        Args:
            collection_name: Name of the collection to clear.

        Raises:
            VectorStoreException: If the clear operation fails.
        """
        try:
            collection = self._get_collection(collection_name)
            all_ids = collection.get()["ids"]
            if all_ids:
                collection.delete(ids=all_ids)
            logger.info(
                "Collection cleared",
                extra={"collection_name": collection_name, "removed_count": len(all_ids)},
            )
        except VectorStoreException:
            raise
        except Exception as exc:
            logger.error(
                "Failed to clear collection",
                extra={"collection_name": collection_name, "error": str(exc)},
            )
            raise VectorStoreException(
                message=f"Failed to clear collection '{collection_name}'.",
                details={"collection_name": collection_name, "error": str(exc)},
            ) from exc

    # ── Document Operations ────────────────────────

    def add_documents(
        self,
        collection_name: str,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Insert documents with pre-computed embeddings.

        All input lists must have the same length.  Documents are
        inserted in batches to handle large datasets efficiently.

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
        self._validate_add_inputs(ids, texts, embeddings, metadatas)

        try:
            collection = self._get_collection(collection_name)
            total = len(ids)
            batch_size = settings.EMBEDDING_BATCH_SIZE

            logger.info(
                "Document insertion started",
                extra={
                    "collection_name": collection_name,
                    "total_documents": total,
                    "batches": -(-total // batch_size),
                },
            )
            start = time.perf_counter()

            for offset in range(0, total, batch_size):
                end = min(offset + batch_size, total)
                collection.add(
                    ids=ids[offset:end],
                    documents=texts[offset:end],
                    embeddings=embeddings[offset:end],
                    metadatas=[self._flatten_metadata(m) for m in metadatas[offset:end]],
                )

            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "Document insertion completed",
                extra={
                    "collection_name": collection_name,
                    "total_documents": total,
                    "elapsed_ms": elapsed_ms,
                },
            )
        except (ValidationException, VectorStoreException):
            raise
        except Exception as exc:
            logger.error(
                "Document insertion failed",
                extra={"collection_name": collection_name, "error": str(exc)},
            )
            raise VectorStoreException(
                message=f"Failed to add documents to '{collection_name}'.",
                details={"collection_name": collection_name, "error": str(exc)},
            ) from exc

    def delete_documents(self, collection_name: str, ids: list[str]) -> None:
        """Remove documents by their IDs.

        Missing IDs are silently ignored.

        Args:
            collection_name: Target collection.
            ids:             Document identifiers to remove.

        Raises:
            ValidationException: If ``ids`` is empty.
            VectorStoreException: If the deletion fails.
        """
        if not ids:
            raise ValidationException(
                message="Document ID list must not be empty.",
                details={"field": "ids"},
            )

        try:
            collection = self._get_collection(collection_name)
            collection.delete(ids=ids)
            logger.info(
                "Documents deleted",
                extra={"collection_name": collection_name, "count": len(ids)},
            )
        except (ValidationException, VectorStoreException):
            raise
        except Exception as exc:
            logger.error(
                "Document deletion failed",
                extra={"collection_name": collection_name, "error": str(exc)},
            )
            raise VectorStoreException(
                message=f"Failed to delete documents from '{collection_name}'.",
                details={"collection_name": collection_name, "error": str(exc)},
            ) from exc

    def update_documents(
        self,
        collection_name: str,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Update existing documents by their IDs.

        All input lists must have the same length.  Documents are
        updated in batches to handle large datasets efficiently.

        Args:
            collection_name: Target collection.
            ids:             Document identifiers to update.
            texts:           Replacement text content.
            embeddings:      Replacement embedding vectors.
            metadatas:       Replacement metadata dictionaries.

        Raises:
            ValidationException: If input lists have mismatched lengths or
                                 contain invalid data.
            VectorStoreException: If the update fails.
        """
        self._validate_add_inputs(ids, texts, embeddings, metadatas)

        try:
            collection = self._get_collection(collection_name)
            total = len(ids)
            batch_size = settings.EMBEDDING_BATCH_SIZE

            logger.info(
                "Document update started",
                extra={
                    "collection_name": collection_name,
                    "total_documents": total,
                    "batches": -(-total // batch_size),
                },
            )
            start = time.perf_counter()

            for offset in range(0, total, batch_size):
                end = min(offset + batch_size, total)
                collection.update(
                    ids=ids[offset:end],
                    documents=texts[offset:end],
                    embeddings=embeddings[offset:end],
                    metadatas=[self._flatten_metadata(m) for m in metadatas[offset:end]],
                )

            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "Document update completed",
                extra={
                    "collection_name": collection_name,
                    "total_documents": total,
                    "elapsed_ms": elapsed_ms,
                },
            )
        except (ValidationException, VectorStoreException):
            raise
        except Exception as exc:
            logger.error(
                "Document update failed",
                extra={"collection_name": collection_name, "error": str(exc)},
            )
            raise VectorStoreException(
                message=f"Failed to update documents in '{collection_name}'.",
                details={"collection_name": collection_name, "error": str(exc)},
            ) from exc

    # ── Search ─────────────────────────────────────

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
            A list of ``RetrievedChunk`` objects ordered by relevance.

        Raises:
            ValidationException: If ``query_embedding`` is empty or
                                 ``top_k`` is not positive.
            VectorStoreException: If the search fails.
        """
        self._validate_search_inputs(query_embedding, top_k)

        try:
            collection = self._get_collection(collection_name)

            logger.info(
                "Similarity search started",
                extra={
                    "collection_name": collection_name,
                    "top_k": top_k,
                    "embedding_dim": len(query_embedding),
                },
            )
            start = time.perf_counter()

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )

            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "Similarity search completed",
                extra={
                    "collection_name": collection_name,
                    "results_count": len(results.get("ids", [[]])[0]),
                    "elapsed_ms": elapsed_ms,
                },
            )

            return self._parse_search_results(results)
        except (ValidationException, VectorStoreException):
            raise
        except Exception as exc:
            logger.error(
                "Similarity search failed",
                extra={"collection_name": collection_name, "error": str(exc)},
            )
            raise VectorStoreException(
                message=f"Similarity search failed on '{collection_name}'.",
                details={"collection_name": collection_name, "error": str(exc)},
            ) from exc

    # ── Internal helpers ───────────────────────────

    @staticmethod
    def _validate_add_inputs(
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Validate input lists for ``add_documents``.

        Raises:
            ValidationException: If any validation rule is violated.
        """
        if not ids:
            raise ValidationException(
                message="Document ID list must not be empty.",
                details={"field": "ids"},
            )

        lengths = {"ids": len(ids), "texts": len(texts), "embeddings": len(embeddings), "metadatas": len(metadatas)}
        unique_lengths = set(lengths.values())
        if len(unique_lengths) != 1:
            raise ValidationException(
                message="Input lists must have the same length.",
                details={"lengths": lengths},
            )

        for idx, doc_id in enumerate(ids):
            if not doc_id or not str(doc_id).strip():
                raise ValidationException(
                    message="Document ID must not be empty.",
                    details={"field": "ids", "index": idx},
                )

        for idx, emb in enumerate(embeddings):
            if not emb:
                raise ValidationException(
                    message="Embedding vector must not be empty.",
                    details={"field": "embeddings", "index": idx},
                )

    @staticmethod
    def _validate_search_inputs(query_embedding: list[float], top_k: int) -> None:
        """Validate inputs for ``similarity_search``.

        Raises:
            ValidationException: If any validation rule is violated.
        """
        if not query_embedding:
            raise ValidationException(
                message="Query embedding must not be empty.",
                details={"field": "query_embedding"},
            )
        if top_k <= 0:
            raise ValidationException(
                message="top_k must be a positive integer.",
                details={"field": "top_k", "value": top_k},
            )

    @staticmethod
    def _flatten_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
        """Flatten a metadata dictionary for ChromaDB storage.

        ChromaDB only supports scalar values (str | int | float | bool).
        Nested dicts and lists are serialised to JSON strings.

        Args:
            metadata: Arbitrary metadata dictionary.

        Returns:
            A flat dictionary with only ChromaDB-compatible values.
        """
        import json

        flat: dict[str, Any] = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                flat[key] = value
            elif value is None:
                flat[key] = ""
            else:
                flat[key] = json.dumps(value, default=str)
        return flat

    @staticmethod
    def _parse_search_results(results: dict[str, Any]) -> list[RetrievedChunk]:
        """Transform raw ChromaDB query results into ``RetrievedChunk`` objects.

        Args:
            results: Raw dictionary returned by ``collection.query()``.

        Returns:
            A list of ``RetrievedChunk`` objects in relevance order.
        """
        chunks: list[RetrievedChunk] = []

        ids_list = results.get("ids", [[]])[0]
        documents_list = results.get("documents", [[]])[0]
        metadatas_list = results.get("metadatas", [[]])[0]
        distances_list = results.get("distances", [[]])[0]

        for idx, chunk_id in enumerate(ids_list):
            distance = distances_list[idx] if idx < len(distances_list) else 0.0
            similarity = max(0.0, 1.0 - (distance / _CHROMA_DISTANCE_CUTOFF))

            chunks.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    text=documents_list[idx] if idx < len(documents_list) else "",
                    metadata=metadatas_list[idx] if idx < len(metadatas_list) else {},
                    score=round(similarity, 4),
                    distance=round(distance, 4),
                )
            )

        return chunks
