"""
Vector Store Layer – Abstract interface and ChromaDB implementation.

This package follows Clean Architecture principles:
  - ``base.py`` defines the ``VectorStore`` ABC and ``RetrievedChunk`` model.
  - ``chroma_store.py`` provides the ChromaDB persistent implementation.
  - Business code should depend only on ``VectorStore``, never on
    the concrete class directly.
"""

from app.vectorstore.base import RetrievedChunk, VectorStore
from app.vectorstore.chroma_store import ChromaVectorStore

__all__: list[str] = [
    "VectorStore",
    "ChromaVectorStore",
    "RetrievedChunk",
]
