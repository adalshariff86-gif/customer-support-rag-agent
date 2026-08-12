"""
Retrieval Service Tests (mocked).

Verifies:
- top_k parameter handling
- Empty query validation
- Empty results handling
- Duplicate chunk filtering
- Context formatting
- Document count property
"""

import pytest

from app.core.exceptions import RetrievalException, ValidationException
from app.services.retrieval_service import (
    RetrievalService,
)
from app.vectorstore.base import RetrievedChunk


@pytest.fixture()
def retrieval_service(mock_embedding_provider, mock_vector_store) -> RetrievalService:
    """RetrievalService wired to mock dependencies."""
    return RetrievalService(
        embedding_provider=mock_embedding_provider,
        vector_store=mock_vector_store,
    )


class TestQueryValidation:
    def test_empty_query_raises(self, retrieval_service: RetrievalService):
        with pytest.raises(ValidationException):
            retrieval_service.retrieve(query="")

    def test_whitespace_query_raises(self, retrieval_service: RetrievalService):
        with pytest.raises(ValidationException):
            retrieval_service.retrieve(query="   ")

    def test_none_query_raises(self, retrieval_service: RetrievalService):
        with pytest.raises(ValidationException):
            retrieval_service.retrieve(query=None)

    def test_zero_top_k_raises(self, retrieval_service: RetrievalService):
        with pytest.raises(ValidationException):
            retrieval_service.retrieve(query="test", top_k=0)

    def test_negative_top_k_raises(self, retrieval_service: RetrievalService):
        with pytest.raises(ValidationException):
            retrieval_service.retrieve(query="test", top_k=-1)


class TestEmbeddingGeneration:
    def test_calls_embedding_provider(
        self, retrieval_service: RetrievalService, mock_embedding_provider
    ):
        retrieval_service.retrieve(query="test query")
        mock_embedding_provider.embed_query.assert_called_once_with("test query")

    def test_embedding_failure_wraps_exception(
        self, retrieval_service: RetrievalService, mock_embedding_provider
    ):
        mock_embedding_provider.embed_query.side_effect = RuntimeError("model crashed")
        with pytest.raises(RetrievalException):
            retrieval_service.retrieve(query="test")


class TestVectorStoreSearch:
    def test_calls_similarity_search(
        self, retrieval_service: RetrievalService, mock_vector_store
    ):
        retrieval_service.retrieve(query="test", top_k=3)
        mock_vector_store.similarity_search.assert_called_once()

    def test_custom_collection_name(
        self, retrieval_service: RetrievalService, mock_vector_store
    ):
        retrieval_service.retrieve(query="test", collection_name="custom")
        call_kwargs = mock_vector_store.similarity_search.call_args
        assert call_kwargs.kwargs["collection_name"] == "custom"


class TestChunkFiltering:
    def test_empty_text_filtered(
        self, retrieval_service: RetrievalService, mock_vector_store
    ):
        mock_vector_store.similarity_search.return_value = [
            RetrievedChunk(
                chunk_id="c1", text="", metadata={}, score=0.9, distance=0.1
            ),
            RetrievedChunk(
                chunk_id="c2", text="valid", metadata={}, score=0.8, distance=0.2
            ),
        ]
        ctx = retrieval_service.retrieve(query="test")
        assert len(ctx.documents) == 1
        assert ctx.documents[0].id == "c2"

    def test_whitespace_text_filtered(
        self, retrieval_service: RetrievalService, mock_vector_store
    ):
        mock_vector_store.similarity_search.return_value = [
            RetrievedChunk(
                chunk_id="c1", text="  ", metadata={}, score=0.9, distance=0.1
            ),
        ]
        ctx = retrieval_service.retrieve(query="test")
        assert len(ctx.documents) == 0

    def test_duplicate_ids_filtered(
        self, retrieval_service: RetrievalService, mock_vector_store
    ):
        mock_vector_store.similarity_search.return_value = [
            RetrievedChunk(
                chunk_id="c1", text="first", metadata={}, score=0.9, distance=0.1
            ),
            RetrievedChunk(
                chunk_id="c1", text="duplicate", metadata={}, score=0.8, distance=0.2
            ),
        ]
        ctx = retrieval_service.retrieve(query="test")
        assert len(ctx.documents) == 1
        assert ctx.documents[0].content == "first"

    def test_empty_metadata_filtered(
        self, retrieval_service: RetrievalService, mock_vector_store
    ):
        mock_vector_store.similarity_search.return_value = [
            RetrievedChunk(
                chunk_id="c1",
                text="valid",
                metadata="not-a-dict",
                score=0.9,
                distance=0.1,
            ),
        ]
        ctx = retrieval_service.retrieve(query="test")
        assert len(ctx.documents) == 0

    def test_empty_chunk_id_filtered(
        self, retrieval_service: RetrievalService, mock_vector_store
    ):
        mock_vector_store.similarity_search.return_value = [
            RetrievedChunk(
                chunk_id="", text="valid", metadata={}, score=0.9, distance=0.1
            ),
        ]
        ctx = retrieval_service.retrieve(query="test")
        assert len(ctx.documents) == 0


class TestEmptyResults:
    def test_no_results_returns_empty_context(
        self, retrieval_service: RetrievalService, mock_vector_store
    ):
        mock_vector_store.similarity_search.return_value = []
        ctx = retrieval_service.retrieve(query="test")
        assert ctx.documents == []
        assert ctx.context == ""
        assert ctx.document_count == 0

    def test_all_filtered_returns_empty_context(
        self, retrieval_service: RetrievalService, mock_vector_store
    ):
        mock_vector_store.similarity_search.return_value = [
            RetrievedChunk(
                chunk_id="c1", text="", metadata={}, score=0.9, distance=0.1
            ),
        ]
        ctx = retrieval_service.retrieve(query="test")
        assert ctx.documents == []
        assert ctx.context == ""


class TestContextFormatting:
    def test_context_contains_documents(
        self, retrieval_service: RetrievalService, mock_vector_store
    ):
        mock_vector_store.similarity_search.return_value = [
            RetrievedChunk(
                chunk_id="c1",
                text="Password reset guide.",
                metadata={"source": "faq.md"},
                score=0.95,
                distance=0.05,
            ),
        ]
        ctx = retrieval_service.retrieve(query="reset password")
        assert "Document: faq.md" in ctx.context
        assert "Password reset guide." in ctx.context

    def test_context_separator(
        self, retrieval_service: RetrievalService, mock_vector_store
    ):
        mock_vector_store.similarity_search.return_value = [
            RetrievedChunk(
                chunk_id="c1",
                text="first",
                metadata={"source": "a.md"},
                score=0.9,
                distance=0.1,
            ),
            RetrievedChunk(
                chunk_id="c2",
                text="second",
                metadata={"source": "b.md"},
                score=0.8,
                distance=0.2,
            ),
        ]
        ctx = retrieval_service.retrieve(query="test")
        assert "------------------------------------" in ctx.context

    def test_context_uses_id_when_no_source(
        self, retrieval_service: RetrievalService, mock_vector_store
    ):
        mock_vector_store.similarity_search.return_value = [
            RetrievedChunk(
                chunk_id="c1", text="text", metadata={}, score=0.9, distance=0.1
            ),
        ]
        ctx = retrieval_service.retrieve(query="test")
        assert "Document: c1" in ctx.context

    def test_document_count_property(
        self, retrieval_service: RetrievalService, mock_vector_store
    ):
        mock_vector_store.similarity_search.return_value = [
            RetrievedChunk(
                chunk_id="c1", text="a", metadata={}, score=0.9, distance=0.1
            ),
            RetrievedChunk(
                chunk_id="c2", text="b", metadata={}, score=0.8, distance=0.2
            ),
        ]
        ctx = retrieval_service.retrieve(query="test")
        assert ctx.document_count == 2

    def test_retrieved_document_conversion(
        self, retrieval_service: RetrievalService, mock_vector_store
    ):
        mock_vector_store.similarity_search.return_value = [
            RetrievedChunk(
                chunk_id="c1",
                text="  content  ",
                metadata={"key": "val"},
                score=0.9,
                distance=0.1,
            ),
        ]
        ctx = retrieval_service.retrieve(query="test")
        doc = ctx.documents[0]
        assert doc.id == "c1"
        assert doc.content == "content"  # stripped
        assert doc.metadata == {"key": "val"}
