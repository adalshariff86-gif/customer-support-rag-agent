"""
Chat API Router – HTTP layer for the customer support RAG agent.

Endpoints:
  POST /chat        – Send a message and receive an AI-generated answer.
  POST /chat/new    – Create a new conversation session.
  GET  /chat/health – Lightweight chat service health check.

Design principles:
  - Thin API layer: validates HTTP requests, calls ChatService, returns responses.
  - No business logic, no retrieval, no embeddings, no memory, no prompt engineering.
  - All domain exceptions (AppException subclasses) are mapped to HTTP responses
    by the global exception handler registered in main.py.
"""

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.dependencies import get_chat_service
from app.core.logger import get_logger
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


# ── Response Models ────────────────────────────────
class NewChatResponse(BaseModel):
    """Response payload for session creation.

    Attributes:
        session_id: Newly created session UUID.
        created: Always true on success.
    """

    session_id: str = Field(
        ...,
        description="Newly created session UUID.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    created: bool = Field(
        default=True,
        description="Indicates successful session creation.",
        examples=[True],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "created": True,
                }
            ]
        }
    }


class ChatHealthResponse(BaseModel):
    """Health check response for the chat service.

    Attributes:
        status: Service health status.
        service: Service identifier.
        timestamp: UTC ISO 8601 timestamp.
        version: Service version string.
    """

    status: str = Field(
        default="healthy",
        description="Service health status.",
        examples=["healthy"],
    )
    service: str = Field(
        default="chat",
        description="Service identifier.",
        examples=["chat"],
    )
    timestamp: str = Field(
        ...,
        description="UTC ISO 8601 timestamp.",
        examples=["2024-01-15T10:30:45.123456+00:00"],
    )
    version: str = Field(
        ...,
        description="Service version string.",
        examples=["1.0.0"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "service": "chat",
                    "timestamp": "2024-01-15T10:30:45.123456+00:00",
                    "version": "1.0.0",
                }
            ]
        }
    }


# ── POST /chat ────────────────────────────────────
@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message",
    description=(
        "Send a user message through the RAG pipeline and receive an "
        "AI-generated response grounded in the knowledge base.  If no "
        "session_id is provided, a new session is created automatically."
    ),
    responses={
        200: {
            "description": "Successful chat response with answer and source documents.",
            "model": ChatResponse,
        },
        422: {"description": "Validation error (empty message, invalid session_id)."},
        502: {"description": "Upstream LLM provider failure."},
        500: {"description": "Internal server error."},
    },
)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Process a chat message through the RAG pipeline.

    Delegates entirely to ChatService.chat().  No business logic is
    executed in this handler.
    """
    start_time = time.perf_counter()

    logger.info(
        "Request received",
        extra={
            "endpoint": "POST /chat",
            "query_length": len(request.message),
            "session_id": request.session_id or "new",
        },
    )

    response = chat_service.chat(request)

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(
        "Request completed",
        extra={
            "endpoint": "POST /chat",
            "status_code": 200,
            "elapsed_ms": elapsed_ms,
            "session_id": response.session_id,
            "query_length": len(request.message),
        },
    )

    return response


# ── POST /chat/new ────────────────────────────────
@router.post(
    "/new",
    response_model=NewChatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session",
    description=(
        "Create a new conversation session and return its UUID.  "
        "Use the returned session_id in subsequent /chat requests."
    ),
    responses={
        201: {
            "description": "Session created successfully.",
            "model": NewChatResponse,
        },
        500: {"description": "Internal server error."},
    },
)
async def new_chat(
    chat_service: ChatService = Depends(get_chat_service),
) -> NewChatResponse:
    """Create a new conversation session.

    Delegates entirely to ChatService.new_chat().  No business logic is
    executed in this handler.
    """
    start_time = time.perf_counter()

    logger.info(
        "Request received",
        extra={"endpoint": "POST /chat/new"},
    )

    session_id = chat_service.new_chat()

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(
        "Request completed",
        extra={
            "endpoint": "POST /chat/new",
            "status_code": 201,
            "elapsed_ms": elapsed_ms,
            "session_id": session_id,
        },
    )

    return NewChatResponse(session_id=session_id, created=True)


# ── GET /chat/health ──────────────────────────────
@router.get(
    "/health",
    response_model=ChatHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat service health check",
    description=(
        "Lightweight health check for the chat service.  "
        "Returns service status, version, and UTC timestamp."
    ),
    responses={
        200: {
            "description": "Service is healthy.",
            "model": ChatHealthResponse,
        },
    },
)
async def health_check(
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatHealthResponse:
    """Return chat service health status.

    Delegates entirely to ChatService.health_check().  No external API
    calls or database writes are performed.
    """
    start_time = time.perf_counter()

    health = chat_service.health_check()

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(
        "Request completed",
        extra={
            "endpoint": "GET /chat/health",
            "status_code": 200,
            "elapsed_ms": elapsed_ms,
        },
    )

    return ChatHealthResponse(
        status=health.get("status", "healthy"),
        service=health.get("service", "chat"),
        timestamp=health.get(
            "timestamp", datetime.now(timezone.utc).isoformat()
        ),
        version=health.get("version", settings.APP_ENV),
    )
