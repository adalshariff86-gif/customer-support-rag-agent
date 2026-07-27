"""
Sentence-Transformer Embedding Provider – Concrete implementation.

Loads the model once (lazy singleton) and provides thread-safe embedding
generation via batching.  Follows Clean Architecture by implementing the
``EmbeddingProvider`` ABC.

Usage:
    from app.embeddings import SentenceTransformerEmbeddingProvider

    provider = SentenceTransformerEmbeddingProvider(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        batch_size=32,
        device="cpu",
    )
    vector = provider.embed_query("Hello world")
"""

import time
from threading import Lock

from app.core.config import settings
from app.core.exceptions import EmbeddingException, ValidationException
from app.core.logger import get_logger
from app.embeddings.base import EmbeddingProvider

logger = get_logger(__name__)


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """Sentence-Transformer based embedding provider.

    Attributes:
        model_name: HuggingFace model identifier.
        batch_size: Number of texts to embed per batch.
        device:     Compute device (``cpu`` or ``cuda``).
    """

    _model = None  # class-level; loaded once per process
    _model_lock = Lock()
    _dimension: int | None = None

    def __init__(
        self,
        model_name: str | None = None,
        batch_size: int | None = None,
        device: str | None = None,
    ) -> None:
        """Initialise the provider with optional overrides.

        Args:
            model_name: HuggingFace model ID. Defaults to config value.
            batch_size: Embedding batch size. Defaults to config value.
            device:     Compute device. Defaults to config value.
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        self.device = device or settings.EMBEDDING_DEVICE

    def _load_model(self) -> None:
        """Lazy-load the SentenceTransformer model (thread-safe, once only)."""
        if SentenceTransformerEmbeddingProvider._model is not None:
            return

        with SentenceTransformerEmbeddingProvider._model_lock:
            # Double-check after acquiring the lock
            if SentenceTransformerEmbeddingProvider._model is not None:
                return

            try:
                from sentence_transformers import SentenceTransformer

                logger.info(
                    "Loading embedding model",
                    extra={"model_name": self.model_name, "device": self.device},
                )
                SentenceTransformerEmbeddingProvider._model = SentenceTransformer(
                    self.model_name, device=self.device
                )
                SentenceTransformerEmbeddingProvider._dimension = (
                    SentenceTransformerEmbeddingProvider._model.get_sentence_embedding_dimension()
                )
                logger.info(
                    "Embedding model loaded",
                    extra={
                        "model_name": self.model_name,
                        "dimension": SentenceTransformerEmbeddingProvider._dimension,
                    },
                )
            except Exception as exc:
                logger.error(
                    "Failed to load embedding model",
                    extra={"model_name": self.model_name, "error": str(exc)},
                )
                raise EmbeddingException(
                    message=f"Failed to load embedding model '{self.model_name}'.",
                    details={"model_name": self.model_name, "error": str(exc)},
                ) from exc

    @property
    def _ensure_model(self):
        """Ensure the model is loaded and return it."""
        self._load_model()
        return SentenceTransformerEmbeddingProvider._model

    def embed_query(self, text: str) -> list[float]:
        """Generate an embedding vector for a single query string.

        Args:
            text: The input text to embed.

        Returns:
            A list of floats representing the embedding vector.

        Raises:
            ValidationException: If ``text`` is empty or whitespace-only.
            EmbeddingException:  If the model fails to generate the embedding.
        """
        if not text or not text.strip():
            raise ValidationException(
                message="Query text must not be empty.",
                details={"field": "text"},
            )

        try:
            model = self._ensure_model
            logger.info("Embedding started", extra={"type": "query", "text_length": len(text)})
            start = time.perf_counter()

            vector = model.encode(
                [text],
                batch_size=1,
                show_progress_bar=False,
                convert_to_numpy=True,
            )

            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "Embedding completed",
                extra={"type": "query", "elapsed_ms": elapsed_ms, "dimension": len(vector[0])},
            )
            return vector[0].tolist()
        except ValidationException:
            raise
        except EmbeddingException:
            raise
        except Exception as exc:
            logger.error(
                "Embedding failed",
                extra={"type": "query", "error": str(exc)},
            )
            raise EmbeddingException(
                message="Failed to generate query embedding.",
                details={"error": str(exc)},
            ) from exc

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of document strings.

        Uses internal batching to process large lists efficiently.

        Args:
            texts: A list of input texts to embed.

        Returns:
            A list of embedding vectors, one per input text.

        Raises:
            ValidationException: If ``texts`` is empty.
            EmbeddingException:  If the model fails to generate embeddings.
        """
        if not texts:
            raise ValidationException(
                message="Document list must not be empty.",
                details={"field": "texts"},
            )

        try:
            model = self._ensure_model
            total = len(texts)
            logger.info(
                "Embedding started",
                extra={"type": "documents", "batch_size": total},
            )
            start = time.perf_counter()

            all_vectors: list[list[float]] = []
            for offset in range(0, total, self.batch_size):
                batch = texts[offset : offset + self.batch_size]
                vectors = model.encode(
                    batch,
                    batch_size=self.batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                all_vectors.extend(v.tolist() for v in vectors)

            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "Embedding completed",
                extra={
                    "type": "documents",
                    "total_documents": total,
                    "batches": -(-total // self.batch_size),  # ceil division
                    "elapsed_ms": elapsed_ms,
                },
            )
            return all_vectors
        except ValidationException:
            raise
        except EmbeddingException:
            raise
        except Exception as exc:
            logger.error(
                "Embedding failed",
                extra={"type": "documents", "error": str(exc)},
            )
            raise EmbeddingException(
                message="Failed to generate document embeddings.",
                details={"error": str(exc)},
            ) from exc

    def dimension(self) -> int:
        """Return the dimensionality of the embedding vectors.

        Returns:
            An integer representing the vector size.

        Raises:
            EmbeddingException: If the model cannot report its dimension.
        """
        try:
            self._load_model()
            assert SentenceTransformerEmbeddingProvider._dimension is not None
            return SentenceTransformerEmbeddingProvider._dimension
        except EmbeddingException:
            raise
        except Exception as exc:
            raise EmbeddingException(
                message="Failed to retrieve embedding dimension.",
                details={"error": str(exc)},
            ) from exc
