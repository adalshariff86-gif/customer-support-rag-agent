"""
Chat API routes for the customer support RAG agent.

Responsibilities:
- Accept HTTP requests.
- Validate request schemas through Pydantic.
- Delegate business operations to ChatService.
- Convert business exceptions into HTTP responses.

This module contains NO:
- RAG logic
- Retrieval logic
- Vector search
- Embedding generation
- Prompt engineering
- Memory implementation
- LLM implementation
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.exceptions import (
    ChatException,
    LLMException,
    MemoryException,
    RAGException,
    RetrievalException,
    ValidationException,
)
from app.core.logger import get_logger
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


# ----------------------------------------------------------------------
# Dependency Injection
# ----------------------------------------------------------------------

from app.core.dependencies import get_chat_service


# ----------------------------------------------------------------------
# POST /chat
# ----------------------------------------------------------------------

@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """
    Send a message to the customer support assistant.

    Session behaviour:
    - If session_id is omitted or empty, a new session is created.
    - If session_id is supplied and exists, the conversation continues.
    - If session_id is supplied but does not exist, a 404 is returned.
    """

    try:
        logger.info(
            "POST /chat request received",
            extra={
                "session_id": request.session_id or "new",
                "message_length": len(request.message),
            },
        )

        response = service.chat(request)

        logger.info(
            "POST /chat request completed",
            extra={
                "session_id": response.session_id,
            },
        )

        return response

    except ValidationException as exc:
        logger.warning(
            "Chat request validation failed",
            extra={"error": str(exc)},
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_exception_detail(exc),
        ) from exc

    except MemoryException as exc:
        logger.warning(
            "Chat memory error",
            extra={"error": str(exc)},
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_exception_detail(exc),
        ) from exc

    except RetrievalException as exc:
        logger.error(
            "Chat retrieval error",
            extra={"error": str(exc)},
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_exception_detail(exc),
        ) from exc

    except LLMException as exc:
        logger.error(
            "Chat LLM error",
            extra={"error": str(exc)},
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_exception_detail(exc),
        ) from exc

    except RAGException as exc:
        logger.error(
            "Chat RAG error",
            extra={"error": str(exc)},
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_exception_detail(exc),
        ) from exc

    except ChatException as exc:
        logger.error(
            "Chat service error",
            extra={"error": str(exc)},
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_exception_detail(exc),
        ) from exc


# ----------------------------------------------------------------------
# POST /chat/new
# ----------------------------------------------------------------------

@router.post(
    "/new",
    status_code=status.HTTP_201_CREATED,
)
def new_chat(
    service: ChatService = Depends(get_chat_service),
) -> dict:
    """
    Explicitly create a new chat session.
    """

    try:
        logger.info("POST /chat/new request received")

        session_id = service.new_chat()

        logger.info(
            "New chat session created",
            extra={"session_id": session_id},
        )

        return {
            "session_id": session_id,
            "created": True,
        }

    except MemoryException as exc:
        logger.error(
            "Failed to create new chat session",
            extra={"error": str(exc)},
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_exception_detail(exc),
        ) from exc

    except ChatException as exc:
        logger.error(
            "Chat service failed to create session",
            extra={"error": str(exc)},
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_exception_detail(exc),
        ) from exc


# ----------------------------------------------------------------------
# GET /chat/history/{session_id}
# ----------------------------------------------------------------------

@router.get(
    "/history/{session_id}",
    status_code=status.HTTP_200_OK,
)
def get_chat_history(
    session_id: str,
    service: ChatService = Depends(get_chat_service),
) -> dict:
    """
    Return all messages belonging to a conversation session.

    The session must exist in the current MemoryService instance.
    """

    try:
        logger.info(
            "GET /chat/history request received",
            extra={"session_id": session_id},
        )

        messages = service.get_history(session_id)

        return {
            "session_id": session_id,
            "message_count": len(messages),
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat(),
                    "sources": message.sources,
                }
                for message in messages
            ],
        }

    except ValidationException as exc:
        logger.warning(
            "Invalid history request",
            extra={
                "session_id": session_id,
                "error": str(exc),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_exception_detail(exc),
        ) from exc

    except MemoryException as exc:
        logger.warning(
            "History session not found",
            extra={
                "session_id": session_id,
                "error": str(exc),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_exception_detail(exc),
        ) from exc

    except ChatException as exc:
        logger.error(
            "Failed to retrieve chat history",
            extra={
                "session_id": session_id,
                "error": str(exc),
            },
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_exception_detail(exc),
        ) from exc


# ----------------------------------------------------------------------
# GET /chat/health
# ----------------------------------------------------------------------

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
)
def chat_health(
    service: ChatService = Depends(get_chat_service),
) -> dict:
    """
    Return the health status of the ChatService.
    """

    try:
        return service.health_check()

    except Exception as exc:
        logger.error(
            "Chat health check failed",
            extra={"error": str(exc)},
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Chat service health check failed.",
                "error": str(exc),
            },
        ) from exc


# ----------------------------------------------------------------------
# Exception helper
# ----------------------------------------------------------------------

def _exception_detail(exc: Exception) -> dict:
    """
    Convert application exceptions into a consistent HTTP detail object.

    Supports the custom exception structure used by this project while
    remaining safe if an exception does not expose all attributes.
    """

    detail: dict = {
        "message": str(exc),
    }

    message = getattr(exc, "message", None)
    details = getattr(exc, "details", None)

    if message:
        detail["message"] = message

    if details:
        detail["details"] = details

    return detail
