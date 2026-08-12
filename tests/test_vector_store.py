"""
Vector Store Tests (mocked ChromaDB).

Verifies:
- add_documents
- update_documents
- delete_documents
- similarity_search
- clear_collection
- get_collection_stats
- create/delete/collection_exists
- reset
"""

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import ValidationException


@pytest.fixture()
def mock_chroma_client():
    """Mock ChromaDB PersistentClient."""
    client = MagicMock()
    client.list_collections.return_value = []
    client.get_or_create_collection.return_value = MagicMock()
    client.get_collection.return_value = MagicMock()
    return client


@pytest.fixture()
def vector_store(mock_chroma_client):
    """ChromaVectorStore with mocked ChromaDB client."""
    with patch("app.vectorstore.chroma_store.chromadb", create=True):
        from app.vectorstore.chroma_store import ChromaVectorStore

        store = ChromaVectorStore(persist_directory="/tmp/test_chroma")
        # Override the class-level client
        ChromaVectorStore._client = mock_chroma_client
        yield store
        ChromaVectorStore._client = None


class TestAddDocuments:
    def test_calls_collection_add(self, vector_store, mock_chroma_client):
        mock_collection = MagicMock()
        mock_chroma_client.get_collection.return_value = mock_collection

        vector_store.add_documents(
            collection_name="docs",
            ids=["id1", "id2"],
            texts=["text1", "text2"],
            embeddings=[[0.1] * 384, [0.2] * 384],
            metadatas=[{"source": "a"}, {"source": "b"}],
        )
        mock_collection.add.assert_called_once()

    def test_empty_ids_raises(self, vector_store):
        with pytest.raises(ValidationException):
            vector_store.add_documents(
                collection_name="docs",
                ids=[],
                texts=[],
                embeddings=[],
                metadatas=[],
            )

    def test_mismatched_lengths_raises(self, vector_store):
        with pytest.raises(ValidationException):
            vector_store.add_documents(
                collection_name="docs",
                ids=["id1"],
                texts=["t1", "t2"],
                embeddings=[[0.1]],
                metadatas=[{}],
            )


class TestDeleteDocuments:
    def test_calls_collection_delete(self, vector_store, mock_chroma_client):
        mock_collection = MagicMock()
        mock_chroma_client.get_collection.return_value = mock_collection

        vector_store.delete_documents(collection_name="docs", ids=["id1", "id2"])
        mock_collection.delete.assert_called_once_with(ids=["id1", "id2"])

    def test_empty_ids_raises(self, vector_store):
        with pytest.raises(ValidationException):
            vector_store.delete_documents(collection_name="docs", ids=[])


class TestUpdateDocuments:
    def test_calls_collection_update(self, vector_store, mock_chroma_client):
        mock_collection = MagicMock()
        mock_chroma_client.get_collection.return_value = mock_collection

        vector_store.update_documents(
            collection_name="docs",
            ids=["id1"],
            texts=["updated"],
            embeddings=[[0.3] * 384],
            metadatas=[{"source": "c"}],
        )
        mock_collection.update.assert_called_once()

    def test_empty_ids_raises(self, vector_store):
        with pytest.raises(ValidationException):
            vector_store.update_documents(
                collection_name="docs",
                ids=[],
                texts=[],
                embeddings=[],
                metadatas=[],
            )


class TestSimilaritySearch:
    def test_calls_collection_query(self, vector_store, mock_chroma_client):
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": [["c1"]],
            "documents": [["text"]],
            "metadatas": [[{}]],
            "distances": [[0.5]],
        }
        mock_chroma_client.get_collection.return_value = mock_collection

        results = vector_store.similarity_search(
            collection_name="docs",
            query_embedding=[0.1] * 384,
            top_k=3,
        )
        mock_collection.query.assert_called_once()
        assert len(results) == 1
        assert results[0].chunk_id == "c1"

    def test_empty_query_embedding_raises(self, vector_store):
        with pytest.raises(ValidationException):
            vector_store.similarity_search(
                collection_name="docs",
                query_embedding=[],
                top_k=5,
            )

    def test_negative_top_k_raises(self, vector_store):
        with pytest.raises(ValidationException):
            vector_store.similarity_search(
                collection_name="docs",
                query_embedding=[0.1] * 384,
                top_k=-1,
            )


class TestClearCollection:
    def test_calls_delete_on_all_docs(self, vector_store, mock_chroma_client):
        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": ["id1", "id2"]}
        mock_chroma_client.get_collection.return_value = mock_collection

        vector_store.clear_collection(collection_name="docs")
        mock_collection.delete.assert_called()


class TestGetCollectionStats:
    def test_returns_stats(self, vector_store, mock_chroma_client):
        mock_collection = MagicMock()
        mock_collection.count.return_value = 42
        mock_collection.peek.return_value = {"embeddings": [[0.1] * 384]}
        mock_chroma_client.get_collection.return_value = mock_collection

        stats = vector_store.get_collection_stats(collection_name="docs")
        assert stats["name"] == "docs"
        assert stats["count"] == 42


class TestCollectionManagement:
    def test_create_collection(self, vector_store, mock_chroma_client):
        vector_store.create_collection("new_coll")
        mock_chroma_client.get_or_create_collection.assert_called_once_with(
            name="new_coll"
        )

    def test_collection_exists(self, vector_store, mock_chroma_client):
        mock_coll = MagicMock()
        mock_coll.name = "docs"
        mock_chroma_client.list_collections.return_value = [mock_coll]
        assert vector_store.collection_exists("docs") is True

    def test_collection_not_exists(self, vector_store, mock_chroma_client):
        mock_chroma_client.list_collections.return_value = []
        assert vector_store.collection_exists("docs") is False


class TestReset:
    def test_calls_delete_on_all_collections(self, vector_store, mock_chroma_client):
        coll1 = MagicMock()
        coll1.name = "coll1"
        coll2 = MagicMock()
        coll2.name = "coll2"
        mock_chroma_client.list_collections.return_value = [coll1, coll2]

        vector_store.reset()
        assert mock_chroma_client.delete_collection.call_count == 2
