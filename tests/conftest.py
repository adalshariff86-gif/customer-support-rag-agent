"""
Shared fixtures and mocks for the test suite.

Provides pre-configured mock objects for every service boundary so
individual test files never need to construct or wire dependencies.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import (
    ChatException,
    LLMException,
    MemoryException,
    RAGException,
    RetrievalException,
    ValidationException,
    VectorStoreException,
)
from app.models.chat import ChatRequest, ChatResponse, SourceDocument
from app.services.memory_service import MemoryService
from app.services.retrieval_service import RetrievedContext, RetrievedDocument


# ── UUID Factory ──────────────────────────────────
def _uuid() -> str:
    return str(uuid.uuid4())


# ── Mock Factories ────────────────────────────────
@pytest.fixture()
def mock_llm_provider() -> MagicMock:
    """Mock LLMProvider with a controllable generate() response."""
    llm = MagicMock()
    llm.model_name = "test-model"
    llm.generate.return_value = "Test LLM response"
    return llm


@pytest.fixture()
def mock_embedding_provider() -> MagicMock:
    """Mock EmbeddingProvider returning a fixed-dimension vector."""
    emb = MagicMock()
    emb.embed_query.return_value = [0.1] * 384
    emb.embed_documents.return_value = [[0.1] * 384, [0.2] * 384]
    emb.dimension.return_value = 384
    return emb


@pytest.fixture()
def mock_vector_store() -> MagicMock:
    """Mock VectorStore with stubbed operations."""
    vs = MagicMock()
    vs.similarity_search.return_value = []
    vs.create_collection.return_value = None
    vs.delete_collection.return_value = None
    vs.collection_exists.return_value = True
    vs.count.return_value = 0
    vs.reset.return_value = None
    vs.add_documents.return_value = None
    vs.delete_documents.return_value = None
    vs.update_documents.return_value = None
    vs.get_collection_stats.return_value = {"name": "test", "count": 0}
    vs.clear_collection.return_value = None
    return vs


@pytest.fixture()
def mock_memory_service() -> MagicMock:
    """Mock MemoryService with session stubs."""
    mem = MagicMock(spec=MemoryService)
    mem.create_session.return_value = _uuid()
    mem.session_exists.return_value = True
    mem.add_message.return_value = None
    mem.get_messages.return_value = []
    mem.get_recent_messages.return_value = []
    mem.get_formatted_history.return_value = ""
    mem.clear_session.return_value = None
    mem.delete_session.return_value = None
    mem.list_sessions.return_value = []
    mem.session_count.return_value = 0
    return mem


@pytest.fixture()
def mock_retrieval_service() -> MagicMock:
    """Mock RetrievalService returning a stubbed context."""
    rs = MagicMock()
    rs.retrieve.return_value = RetrievedContext(
        documents=[],
        context="",
        query="test query",
        elapsed_ms=10.0,
    )
    return rs


@pytest.fixture()
def mock_orchestrator() -> MagicMock:
    """Mock RAGOrchestrator with a controllable chat response."""
    orch = MagicMock()
    orch.create_session.return_value = _uuid()
    orch.chat.return_value = ChatResponse(
        session_id=_uuid(),
        answer="Test answer",
        sources=[],
        model="test-model",
        latency_ms=100,
        timestamp=datetime.now(timezone.utc),
    )
    return orch


@pytest.fixture()
def chat_request() -> ChatRequest:
    """A valid ChatRequest for testing."""
    return ChatRequest(message="How do I reset my password?")


@pytest.fixture()
def chat_request_with_session() -> ChatRequest:
    """A ChatRequest with an existing session_id."""
    return ChatRequest(
        session_id=_uuid(),
        message="What are your hours?",
    )


@pytest.fixture()
def sample_retrieved_documents() -> list[RetrievedDocument]:
    """Sample retrieved documents for testing."""
    return [
        RetrievedDocument(
            id="doc_1",
            content="Password reset instructions.",
            score=0.95,
            metadata={"source": "faq.md"},
        ),
        RetrievedDocument(
            id="doc_2",
            content="Account recovery options.",
            score=0.82,
            metadata={"source": "help.md"},
        ),
    ]


@pytest.fixture()
def sample_chat_response() -> ChatResponse:
    """A complete ChatResponse for testing."""
    return ChatResponse(
        session_id=_uuid(),
        answer="To reset your password, visit settings.",
        sources=[
            SourceDocument(
                id="doc_1",
                content="Password reset instructions.",
                score=0.95,
                metadata={"source": "faq.md"},
            )
        ],
        model="test-model",
        latency_ms=250,
        timestamp=datetime.now(timezone.utc),
    )
