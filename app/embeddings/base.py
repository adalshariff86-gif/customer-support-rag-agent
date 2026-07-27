"""
Abstract Embedding Provider – Clean Architecture interface.

All embedding implementations must inherit from ``EmbeddingProvider`` and
implement the three required methods: ``embed_query``, ``embed_documents``,
and ``dimension``.

Usage:
    from app.embeddings.base import EmbeddingProvider

    class MyProvider(EmbeddingProvider):
        def embed_query(self, text: str) -> list[float]:
            ...
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            ...
        def dimension(self) -> int:
            ...
"""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract base class for all embedding providers.

    Every concrete provider (Sentence-Transformer, OpenAI, etc.) must
    implement these three methods.  Business logic should depend only
    on this interface so that providers can be swapped without code changes.
    """

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Generate an embedding vector for a single query string.

        Args:
            text: The input text to embed.

        Returns:
            A list of floats representing the embedding vector.

        Raises:
            ValidationException: If ``text`` is empty.
            EmbeddingException:  If the underlying model fails.
        """

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of document strings.

        Args:
            texts: A list of input texts to embed.

        Returns:
            A list of embedding vectors, one per input text.

        Raises:
            ValidationException: If ``texts`` is empty.
            EmbeddingException:  If the underlying model fails.
        """

    @abstractmethod
    def dimension(self) -> int:
        """Return the dimensionality of the embedding vectors.

        Returns:
            An integer representing the vector size (e.g. 384 for MiniLM).
        """
