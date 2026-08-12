"""
Customer Support RAG Agent – Model Exports.

Public API for Pydantic models used across the application.
"""

from app.models.chat import (
    ChatFeedback,
    ChatRequest,
    ChatResponse,
    SourceDocument,
)
from app.models.error import (
    ErrorResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
)
from app.models.health import (
    DependencyHealth,
    DependencyStatus,
    HealthCheckResponse,
    LivenessResponse,
    ReadinessResponse,
    ReadinessStatus,
)
from app.models.session import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionDeleteResponse,
    SessionHistoryItem,
    SessionHistoryResponse,
)

__all__ = [
    # Chat
    "ChatFeedback",
    "ChatRequest",
    "ChatResponse",
    "SourceDocument",
    # Health
    "DependencyHealth",
    "DependencyStatus",
    "HealthCheckResponse",
    "LivenessResponse",
    "ReadinessResponse",
    "ReadinessStatus",
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
