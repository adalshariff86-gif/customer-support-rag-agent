"""
Embedding Provider Tests (mocked).

Verifies:
- Lazy loading of SentenceTransformer model
- Singleton behavior
- Batch embedding
- Dimension property
- Empty input validation
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import EmbeddingException, ValidationException
from app.embeddings.sentence_transformer import SentenceTransformerEmbeddingProvider


@pytest.fixture(autouse=True)
def reset_class_state():
    """Reset class-level singleton state before each test."""
    SentenceTransformerEmbeddingProvider._model = None
    SentenceTransformerEmbeddingProvider._dimension = None
    yield
    SentenceTransformerEmbeddingProvider._model = None
    SentenceTransformerEmbeddingProvider._dimension = None


@pytest.fixture()
def mock_st_module():
    """Provide a mock sentence_transformers module injected into sys.modules."""
    mock_module = MagicMock()
    with patch.dict(sys.modules, {"sentence_transformers": mock_module}):
        yield mock_module


def _make_mock_model(dimension=384):
    """Create a mock model with configurable behavior."""
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = dimension
    mock_model.encode.return_value = MagicMock(tolist=lambda: [0.1] * dimension)
    return mock_model


class TestLazyLoading:
    def test_model_not_loaded_on_init(self):
        provider = SentenceTransformerEmbeddingProvider(
            model_name="test-model", batch_size=16, device="cpu"
        )
        assert SentenceTransformerEmbeddingProvider._model is None

    def test_model_loaded_on_first_embed(self, mock_st_module):
        mock_model = _make_mock_model()
        mock_st_module.SentenceTransformer.return_value = mock_model

        provider = SentenceTransformerEmbeddingProvider(
            model_name="test-model", batch_size=16, device="cpu"
        )
        provider.embed_query("hello")
        assert SentenceTransformerEmbeddingProvider._model is mock_model

    def test_model_not_reloaded_on_second_call(self, mock_st_module):
        mock_model = _make_mock_model()
        mock_st_module.SentenceTransformer.return_value = mock_model

        provider = SentenceTransformerEmbeddingProvider(
            model_name="test-model", batch_size=16, device="cpu"
        )
        provider.embed_query("hello")
        provider.embed_query("world")
        mock_st_module.SentenceTransformer.assert_called_once()


class TestSingleton:
    def test_shared_model_across_instances(self, mock_st_module):
        mock_model = _make_mock_model()
        mock_st_module.SentenceTransformer.return_value = mock_model

        p1 = SentenceTransformerEmbeddingProvider(model_name="test")
        p1.embed_query("hello")

        p2 = SentenceTransformerEmbeddingProvider(model_name="test")
        p2.embed_query("world")

        mock_st_module.SentenceTransformer.assert_called_once()


class TestBatchEmbedding:
    def test_embed_documents_calls_encode(self, mock_st_module):
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = [
            MagicMock(tolist=lambda: [0.1] * 384),
            MagicMock(tolist=lambda: [0.2] * 384),
        ]
        mock_st_module.SentenceTransformer.return_value = mock_model

        provider = SentenceTransformerEmbeddingProvider(
            model_name="test", batch_size=32, device="cpu"
        )
        result = provider.embed_documents(["doc1", "doc2"])

        assert len(result) == 2
        mock_model.encode.assert_called_once()

    def test_batch_splitting(self, mock_st_module):
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.side_effect = [
            [
                MagicMock(tolist=lambda: [0.1] * 384),
                MagicMock(tolist=lambda: [0.2] * 384),
            ],
            [MagicMock(tolist=lambda: [0.3] * 384)],
        ]
        mock_st_module.SentenceTransformer.return_value = mock_model

        provider = SentenceTransformerEmbeddingProvider(
            model_name="test", batch_size=2, device="cpu"
        )
        result = provider.embed_documents(["d1", "d2", "d3"])

        assert mock_model.encode.call_count == 2
        assert len(result) == 3


class TestDimension:
    def test_returns_dimension(self, mock_st_module):
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_st_module.SentenceTransformer.return_value = mock_model

        provider = SentenceTransformerEmbeddingProvider(model_name="test")
        dim = provider.dimension()
        assert dim == 384


class TestValidation:
    def test_empty_query_raises(self):
        provider = SentenceTransformerEmbeddingProvider(model_name="test")
        with pytest.raises(ValidationException):
            provider.embed_query("")

    def test_whitespace_query_raises(self):
        provider = SentenceTransformerEmbeddingProvider(model_name="test")
        with pytest.raises(ValidationException):
            provider.embed_query("   ")

    def test_empty_documents_raises(self):
        provider = SentenceTransformerEmbeddingProvider(model_name="test")
        with pytest.raises(ValidationException):
            provider.embed_documents([])


class TestModelLoadFailure:
    def test_import_error_raises_embedding_exception(self, mock_st_module):
        mock_st_module.SentenceTransformer.side_effect = ImportError("no module")
        provider = SentenceTransformerEmbeddingProvider(model_name="test")
        with pytest.raises(EmbeddingException):
            provider.embed_query("hello")
