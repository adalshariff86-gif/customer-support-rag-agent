"""
API Endpoint Tests.

Verifies:
- POST /chat success, invalid request, empty query, server error
- POST /chat/new success, server error
- GET /chat/health success
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.exceptions import (
    ChatException,
    LLMException,
    MemoryException,
    ValidationException,
)
from app.models.chat import ChatResponse, SourceDocument


@pytest.fixture()
def mock_chat_service():
    """Mock ChatService for API dependency injection."""
    svc = MagicMock()
    svc.chat.return_value = ChatResponse(
        session_id="550e8400-e29b-41d4-a716-446655440000",
        answer="To reset your password, visit settings.",
        sources=[
            SourceDocument(
                id="doc_1",
                content="Reset instructions.",
                score=0.95,
                metadata={"source": "faq.md"},
            )
        ],
        model="test-model",
        latency_ms=150,
        timestamp=datetime.now(timezone.utc),
    )
    svc.new_chat.return_value = "550e8400-e29b-41d4-a716-446655440000"
    svc.health_check.return_value = {
        "status": "healthy",
        "service": "chat",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }
    return svc


@pytest.fixture()
def client(mock_chat_service):
    """FastAPI TestClient with mocked ChatService dependency and mocked lifespan."""
    from app.main import app
    from app.core.dependencies import get_chat_service

    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service
    # Mock lifecycle so startup/shutdown are no-ops (avoids chromadb import)
    with patch("app.main._lifecycle") as mock_lc:
        mock_lc.startup = AsyncMock()
        mock_lc.shutdown = AsyncMock()
        mock_lc.health_check.return_value = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": "test",
            "version": "1.0.0",
            "uptime_seconds": 0.0,
            "dependencies": [],
        }
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    app.dependency_overrides.clear()


class TestPostChat:
    def test_success(self, client, mock_chat_service):
        response = client.post(
            "/chat",
            json={"message": "How do I reset my password?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "session_id" in data
        assert data["model"] == "test-model"

    def test_with_session_id(self, client, mock_chat_service):
        response = client.post(
            "/chat",
            json={
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Follow up question",
            },
        )
        assert response.status_code == 200
        request = mock_chat_service.chat.call_args[0][0]
        assert request.session_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_empty_message_returns_422(self, client):
        response = client.post("/chat", json={"message": ""})
        assert response.status_code == 422

    def test_missing_message_returns_422(self, client):
        response = client.post("/chat", json={})
        assert response.status_code == 422

    def test_long_message_returns_422(self, client):
        response = client.post("/chat", json={"message": "x" * 4001})
        assert response.status_code == 422

    def test_validation_error_returns_422(self, client, mock_chat_service):
        mock_chat_service.chat.side_effect = ValidationException(message="bad input")
        response = client.post("/chat", json={"message": "test"})
        assert response.status_code == 422

    def test_llm_error_returns_502(self, client, mock_chat_service):
        mock_chat_service.chat.side_effect = LLMException(message="LLM down")
        response = client.post("/chat", json={"message": "test"})
        assert response.status_code == 502

    def test_server_error_returns_500(self, client, mock_chat_service):
        mock_chat_service.chat.side_effect = ChatException(message="internal error")
        response = client.post("/chat", json={"message": "test"})
        assert response.status_code == 500


class TestPostChatNew:
    def test_success(self, client, mock_chat_service):
        response = client.post("/chat/new")
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert data["created"] is True

    def test_server_error_returns_500(self, client, mock_chat_service):
        mock_chat_service.new_chat.side_effect = MemoryException(message="fail")
        response = client.post("/chat/new")
        assert response.status_code == 500


class TestChatHealth:
    def test_success(self, client, mock_chat_service):
        response = client.get("/chat/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "chat"
        assert "timestamp" in data
        assert "version" in data


class TestRootEndpoint:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "customer-support-rag"
        assert data["status"] == "online"


class TestHealthEndpoint:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
