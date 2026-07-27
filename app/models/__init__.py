"""
Customer Support RAG Agent – Model Exports.

Public API for Pydantic models used across the application.
"""

from app.models.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    SourceDocument,
    StreamingChatResponse,
)
from app.models.health import (
    DependencyHealth,
    DependencyStatus,
    HealthCheckResponse,
    LivenessResponse,
    ReadinessResponse,
)
from app.models.error import (
    ErrorResponse,
    ValidationErrorResponse,
    ValidationErrorDetail,
)
from app.models.session import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionHistoryItem,
    SessionHistoryResponse,
    SessionDeleteResponse,
)

__all__ = [
    # Chat
    "ChatRequest",
    "ChatResponse",
    "ChatMessage",
    "SourceDocument",
    "StreamingChatResponse",
    # Health
    "DependencyHealth",
    "DependencyStatus",
    "HealthCheckResponse",
    "LivenessResponse",
    "ReadinessResponse",
    # Error
    "ErrorResponse",
    "ValidationErrorResponse",
    "ValidationErrorDetail",
    # Session
    "SessionCreateRequest",
    "SessionCreateResponse",
    "SessionHistoryItem",
    "SessionHistoryResponse",
    "SessionDeleteResponse",
]