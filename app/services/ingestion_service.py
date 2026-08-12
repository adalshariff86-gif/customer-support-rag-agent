"""
Document Ingestion Service – Orchestrates the full document ingestion pipeline.

Responsibilities:
  - Load documents from a directory via DocumentLoader.
  - Chunk each document via TextChunker.
  - Generate embeddings via EmbeddingProvider.
  - Store vectors in ChromaDB via VectorStore.
  - Provide idempotent ingestion (skip if already populated unless force=True).
  - Report ingestion status and statistics.

Design principles:
  - Single responsibility: only orchestrates the pipeline, no chunking or
    embedding logic here.
  - Idempotent: repeated calls are safe and skip re-ingestion.
  - Graceful: empty directories and errors produce results, never raise.
  - All steps are logged for observability.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.exceptions import VectorStoreException
from app.core.logger import get_logger
from app.embeddings.base import EmbeddingProvider
from app.services.document_loader import DocumentLoader
from app.services.text_chunker import TextChunker
from app.vectorstore.base import VectorStore

logger = get_logger(__name__)


@dataclass
class IngestionResult:
    """Result of a document ingestion run.

    Attributes:
        documents_loaded: Number of documents loaded from disk.
        chunks_created:   Number of text chunks created from the documents.
        vectors_stored:   Number of vectors written to the vector store.
        collection_name:  Target collection name in the vector store.
        elapsed_ms:       Total wall-clock time for the pipeline (milliseconds).
        already_indexed:  True when ingestion was skipped because the
                          collection was already populated.
        message:          Human-readable summary of what happened.
    """

    documents_loaded: int = 0
    chunks_created: int = 0
    vectors_stored: int = 0
    collection_name: str = "documents"
    elapsed_ms: float = 0.0
    already_indexed: bool = False
    message: str = ""


class IngestionService:
    """Orchestrates the full document ingestion pipeline.

    Args:
        document_loader:   A ``DocumentLoader`` instance for reading files.
        text_chunker:      A ``TextChunker`` instance for splitting text.
        embedding_provider: An ``EmbeddingProvider`` for vector generation.
        vector_store:      A ``VectorStore`` backend for persistence.
        collection_name:   Name of the target collection (default ``"documents"``).
    """

    def __init__(
        self,
        document_loader: DocumentLoader,
        text_chunker: TextChunker,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        collection_name: str = "documents",
    ) -> None:
        self._document_loader = document_loader
        self._text_chunker = text_chunker
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._collection_name = collection_name

    # -- Public API --

    def ingest(
        self,
        directory_path: str | Path | None = None,
        force: bool = False,
    ) -> IngestionResult:
        """Run the full ingestion pipeline.

        Steps:
            1. Ensure the target collection exists.
            2. If already populated (and not ``force``), return early.
            3. If ``force``, clear the collection first.
            4. Load documents from the directory.
            5. Chunk each document.
            6. Generate embeddings.
            7. Store vectors in the collection.

        Args:
            directory_path: Directory containing documents to ingest.
                Defaults to ``data/documents``.
            force: If ``True``, re-ingest even if the collection is
                already populated (clears first).

        Returns:
            An ``IngestionResult`` with statistics and a human-readable message.
        """
        start = time.perf_counter()

        if directory_path is None:
            directory_path = Path("data/documents")
        else:
            directory_path = Path(directory_path)

        logger.info(
            "Ingestion started | directory='%s' force=%s collection='%s'",
            str(directory_path),
            force,
            self._collection_name,
        )

        # Step 1: Idempotent skip – check BEFORE creating the collection
        # so that both ingest() and get_status() derive state from the
        # same source of truth (_safe_count / _is_populated).
        if not force and self._is_populated():
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "Ingestion skipped: collection already populated | "
                "collection='%s' elapsed_ms=%.1f",
                self._collection_name,
                elapsed_ms,
            )
            return IngestionResult(
                collection_name=self._collection_name,
                elapsed_ms=elapsed_ms,
                already_indexed=True,
                message=f"Collection '{self._collection_name}' already populated; skipped.",
            )

        # Step 2: Ensure collection exists (create if missing)
        self._ensure_collection()

        # Step 3: Force clear
        if force:
            logger.info(
                "Force mode: clearing collection '%s' before ingestion",
                self._collection_name,
            )
            self._vector_store.clear_collection(self._collection_name)

        # Step 4: Validate directory
        if not directory_path.exists():
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            msg = f"Directory does not exist: {directory_path}"
            logger.warning("Ingestion aborted | %s", msg)
            return IngestionResult(
                collection_name=self._collection_name,
                elapsed_ms=elapsed_ms,
                message=msg,
            )

        if not directory_path.is_dir():
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            msg = f"Path is not a directory: {directory_path}"
            logger.warning("Ingestion aborted | %s", msg)
            return IngestionResult(
                collection_name=self._collection_name,
                elapsed_ms=elapsed_ms,
                message=msg,
            )

        # Step 5: Load documents
        logger.info("Loading documents from '%s'...", str(directory_path))
        documents = self._document_loader.load_directory(directory_path)
        logger.info("Loaded %d document(s)", len(documents))

        if not documents:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            msg = (
                f"No documents found in '{directory_path}'; knowledge base not updated."
            )
            logger.warning("Ingestion warning | %s", msg)
            return IngestionResult(
                collection_name=self._collection_name,
                elapsed_ms=elapsed_ms,
                message=msg,
            )

        # Step 6: Chunk documents
        all_chunks: list[Any] = []
        for doc in documents:
            chunks = self._text_chunker.chunk_document(
                document_id=doc.id,
                content=doc.content,
                source_file=doc.filename,
            )
            all_chunks.extend(chunks)

        logger.info(
            "Created %d chunk(s) from %d document(s)",
            len(all_chunks),
            len(documents),
        )

        if not all_chunks:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            msg = (
                f"Documents loaded ({len(documents)}) but produced no chunks; "
                "knowledge base not updated."
            )
            logger.warning("Ingestion warning | %s", msg)
            return IngestionResult(
                documents_loaded=len(documents),
                collection_name=self._collection_name,
                elapsed_ms=elapsed_ms,
                message=msg,
            )

        # Step 7: Generate embeddings
        texts = [c.text for c in all_chunks]
        ids = [c.chunk_id for c in all_chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "chunk_index": c.chunk_index,
                "source_file": c.metadata.source_file,
                "character_count": c.metadata.character_count,
                "start_char_index": c.metadata.start_char_index,
                "end_char_index": c.metadata.end_char_index,
            }
            for c in all_chunks
        ]

        logger.info("Generating embeddings for %d chunk(s)...", len(texts))
        embeddings = self._embedding_provider.embed_documents(texts)
        logger.info("Embeddings generated")

        # Step 8: Store in vector store
        logger.info(
            "Storing %d vector(s) in collection '%s'...",
            len(ids),
            self._collection_name,
        )
        self._vector_store.add_documents(
            collection_name=self._collection_name,
            ids=ids,
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Vectors stored successfully")

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        msg = (
            f"Ingestion complete | documents={len(documents)} "
            f"chunks={len(all_chunks)} vectors={len(ids)} "
            f"collection='{self._collection_name}' elapsed_ms={elapsed_ms}"
        )
        logger.info("Ingestion completed | %s", msg)

        return IngestionResult(
            documents_loaded=len(documents),
            chunks_created=len(all_chunks),
            vectors_stored=len(ids),
            collection_name=self._collection_name,
            elapsed_ms=elapsed_ms,
            already_indexed=False,
            message=msg,
        )

    def get_status(self) -> dict[str, Any]:
        """Return the current status of the ingestion collection.

        Uses ``_safe_count`` (which delegates to ``vector_store.count``) as
        the single source of truth for document count.  Collection existence
        is checked via ``collection_exists`` which uses the same underlying
        ``_get_collection`` mechanism, ensuring consistency with ``ingest``.

        Returns:
            A dict with ``collection_name``, ``collection_exists``,
            and ``document_count``.
        """
        collection_exists = self._vector_store.collection_exists(self._collection_name)
        document_count = self._safe_count() if collection_exists else 0

        return {
            "collection_name": self._collection_name,
            "collection_exists": collection_exists,
            "document_count": document_count,
        }

    # -- Private Helpers --

    def _ensure_collection(self) -> None:
        """Create the target collection if it does not already exist."""
        logger.debug("Ensuring collection '%s' exists", self._collection_name)
        self._vector_store.create_collection(self._collection_name)

    def _is_populated(self) -> bool:
        """Return True if the collection contains at least one document."""
        return self._safe_count() > 0

    def _safe_count(self) -> int:
        """Return the document count, or 0 on any error."""
        try:
            return self._vector_store.count(self._collection_name)
        except VectorStoreException:
            return 0
        except Exception:  # noqa: BLE001
            return 0
