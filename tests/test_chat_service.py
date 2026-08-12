"""
Chat Service Tests (mocked).

Verifies:
- chat() delegates to orchestrator
- new_chat() delegates to orchestrator
- health_check() returns correct structure
- Validation: empty query
- Exception wrapping
"""

import pytest
from pydantic import ValidationError

from app.core.exceptions import (
    ChatException,
    LLMException,
    MemoryException,
    ValidationException,
)
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService


@pytest.fixture()
def chat_service(mock_orchestrator) -> ChatService:
    """ChatService wired to a mock orchestrator."""
    return ChatService(orchestrator=mock_orchestrator)


class TestChat:
    def test_delegates_to_orchestrator(
        self, chat_service: ChatService, mock_orchestrator, chat_request
    ):
        result = chat_service.chat(chat_request)
        mock_orchestrator.chat.assert_called_once_with(
            session_id=None, query="How do I reset my password?"
        )
        assert isinstance(result, ChatResponse)

    def test_passes_session_id(
        self, chat_service: ChatService, mock_orchestrator, chat_request_with_session
    ):
        chat_service.chat(chat_request_with_session)
        call_kwargs = mock_orchestrator.chat.call_args.kwargs
        assert call_kwargs["session_id"] == chat_request_with_session.session_id

    def test_empty_query_raises(self, chat_service: ChatService):
        with pytest.raises(ValidationError):
            chat_service.chat(ChatRequest(message=""))

    def test_whitespace_query_raises(self, chat_service: ChatService):
        with pytest.raises(ValidationException):
            chat_service.chat(ChatRequest(message="   "))

    def test_orchestrator_error_propagates(
        self, chat_service: ChatService, mock_orchestrator, chat_request
    ):
        mock_orchestrator.chat.side_effect = LLMException(message="LLM down")
        with pytest.raises(LLMException):
            chat_service.chat(chat_request)

    def test_memory_error_propagates(
        self, chat_service: ChatService, mock_orchestrator, chat_request
    ):
        mock_orchestrator.chat.side_effect = MemoryException(message="session gone")
        with pytest.raises(MemoryException):
            chat_service.chat(chat_request)

    def test_unexpected_error_wraps_in_chat_exception(
        self, chat_service: ChatService, mock_orchestrator, chat_request
    ):
        mock_orchestrator.chat.side_effect = RuntimeError("something broke")
        with pytest.raises(ChatException):
            chat_service.chat(chat_request)


class TestNewChat:
    def test_delegates_to_orchestrator(
        self, chat_service: ChatService, mock_orchestrator
    ):
        result = chat_service.new_chat()
        mock_orchestrator.create_session.assert_called_once()
        assert isinstance(result, str)

    def test_memory_error_propagates(
        self, chat_service: ChatService, mock_orchestrator
    ):
        mock_orchestrator.create_session.side_effect = MemoryException(message="fail")
        with pytest.raises(MemoryException):
            chat_service.new_chat()

    def test_unexpected_error_wraps_in_chat_exception(
        self, chat_service: ChatService, mock_orchestrator
    ):
        mock_orchestrator.create_session.side_effect = RuntimeError("boom")
        with pytest.raises(ChatException):
            chat_service.new_chat()


class TestHealthCheck:
    def test_returns_healthy(self, chat_service: ChatService):
        result = chat_service.health_check()
        assert result["status"] == "healthy"
        assert result["service"] == "chat"
        assert "timestamp" in result
        assert "version" in result
