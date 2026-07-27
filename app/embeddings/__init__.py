"""
Embedding Layer – Abstract interface and concrete providers for text embeddings.

This package follows Clean Architecture principles:
  - ``base.py`` defines the ``EmbeddingProvider`` ABC.
  - ``sentence_transformer.py`` provides the Sentence-Transformers implementation.
  - Business code should depend only on ``EmbeddingProvider``, never on
    the concrete class directly.
"""

from app.embeddings.base import EmbeddingProvider
from app.embeddings.sentence_transformer import SentenceTransformerEmbeddingProvider

__all__: list[str] = ["EmbeddingProvider", "SentenceTransformerEmbeddingProvider"]
