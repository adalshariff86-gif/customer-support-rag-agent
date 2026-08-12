"""
Chat Service – Business layer for the customer support RAG agent.

Coordinates client requests and delegates all AI work to the
RAGOrchestrator. Contains NO retrieval logic, NO memory logic,
NO embedding logic, NO vector search, and NO prompt engineering.

Design principles:

- Single Responsibility: validates requests, invokes orchestrator,
  returns responses.
- Dependency Injection: receives only RAGOrchestrator; never
  instantiates services.
- Open/Closed: business rules can be added without modifying
  orchestration logic.
- Clean Architecture: business layer depends on the orchestrator.

Usage:
    from app.services.chat_service import ChatService

    service = ChatService(orchestrator=orchestrator)

    response = service.chat(
        request=ChatRequest(message="Hello")
    )
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

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
from app.services.rag_orchestrator import RAGOrchestrator


logger = get_logger(__name__)


# ── Constants ──────────────────────────────────────

_SERVICE_VERSION: str = "1.1.0"


class ChatService:
    """Business layer for the customer support RAG chat pipeline.

    Validates incoming requests, delegates all AI and retrieval work
    to the injected RAGOrchestrator, and returns structured responses.

    This service contains zero retrieval, memory, embedding, vector
    search, or prompt-engineering logic.

    Args:
        orchestrator: Injected RAG orchestrator for AI pipeline operations.
    """

    def __init__(self, orchestrator: RAGOrchestrator) -> None:
        self._orchestrator = orchestrator

        logger.info(
            "ChatService initialised",
            extra={
                "service_version": _SERVICE_VERSION,
            },
        )

    # ── Public API ─────────────────────────────────

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request through the RAG pipeline.

        A missing session_id is treated as a request for a new
        conversation. If a valid session_id is supplied, the
        orchestrator continues that existing conversation.

        Args:
            request: Validated chat request payload.

        Returns:
            A ChatResponse containing the answer, sources, and metadata.

        Raises:
            ValidationException:
                If the request fails business validation.

            MemoryException:
                If a memory operation fails.

            RetrievalException:
                If knowledge retrieval fails.

            LLMException:
                If LLM generation fails.

            RAGException:
                If the orchestrator pipeline fails.

            ChatException:
                If an unexpected service-level error occurs.
        """
        start_time = time.perf_counter()

        try:
            logger.info(
                "Chat request started",
                extra={
                    "query_length": len(request.message),
                    "has_session_id": bool(
                        request.session_id
                        and request.session_id.strip()
                    ),
                },
            )

            # ── 1. Validate request ─────────────────

            self._validate_request(request)

            # ── 2. Execute RAG pipeline ─────────────

            response = self._execute_chat(request)

            # ── 3. Log completion ────────────────────

            elapsed_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            logger.info(
                "Chat request completed",
                extra={
                    "session_id": response.session_id,
                    "query_length": len(request.message),
                    "elapsed_ms": elapsed_ms,
                },
            )

            return response

        except (
            ValidationException,
            MemoryException,
            RetrievalException,
            LLMException,
            RAGException,
        ):
            raise

        except Exception as exc:
            elapsed_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            logger.error(
                "Chat request failed",
                extra={
                    "query_length": len(request.message),
                    "elapsed_ms": elapsed_ms,
                    "error": str(exc),
                },
                exc_info=True,
            )

            raise ChatException(
                message="An unexpected error occurred in the chat service.",
                details={
                    "error": str(exc),
                    "query_length": len(request.message),
                },
            ) from exc

    def new_chat(self) -> str:
        """Create a new conversation session.

        Delegates session creation to the RAGOrchestrator.

        Returns:
            A new session UUID string.

        Raises:
            MemoryException:
                If session creation fails.

            ChatException:
                If an unexpected error occurs.
        """
        start_time = time.perf_counter()

        try:
            logger.info("New chat session requested")

            session_id = self._orchestrator.create_session()

            elapsed_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            logger.info(
                "New chat session created",
                extra={
                    "session_id": session_id,
                    "elapsed_ms": elapsed_ms,
                },
            )

            return session_id

        except MemoryException:
            raise

        except Exception as exc:
            elapsed_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            logger.error(
                "New chat session creation failed",
                extra={
                    "elapsed_ms": elapsed_ms,
                    "error": str(exc),
                },
                exc_info=True,
            )

            raise ChatException(
                message="Failed to create a new chat session.",
                details={
                    "error": str(exc),
                },
            ) from exc

    def get_history(self, session_id: str) -> list:
        """Retrieve the conversation history for a session.

        Delegates to the RAGOrchestrator which queries MemoryService.

        Args:
            session_id: The session UUID.

        Returns:
            List of MemoryMessage instances.

        Raises:
            ValidationException:
                If session_id is invalid.

            MemoryException:
                If the session does not exist or memory retrieval fails.

            ChatException:
                If an unexpected error occurs.
        """
        start_time = time.perf_counter()

        try:
            logger.info(
                "History retrieval started",
                extra={"session_id": session_id},
            )

            messages = self._orchestrator.get_session_messages(session_id)

            elapsed_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            logger.info(
                "History retrieval completed",
                extra={
                    "session_id": session_id,
                    "message_count": len(messages),
                    "elapsed_ms": elapsed_ms,
                },
            )

            return messages

        except (ValidationException, MemoryException):
            raise

        except Exception as exc:
            elapsed_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            logger.error(
                "History retrieval failed",
                extra={
                    "session_id": session_id,
                    "elapsed_ms": elapsed_ms,
                    "error": str(exc),
                },
                exc_info=True,
            )

            raise ChatException(
                message="Failed to retrieve chat history.",
                details={
                    "session_id": session_id,
                    "error": str(exc),
                },
            ) from exc

    def health_check(self) -> dict[str, Any]:
        """Return service health status without external calls.

        Returns:
            A dictionary containing service health information.
        """
        return self._build_health_response()

    # ── Private Helpers ─────────────────────────────

    def _validate_request(self, request: ChatRequest) -> None:
        """Validate the incoming chat request.

        Pydantic handles structural validation. This method handles
        business-level validation.

        The session_id is optional. An absent or blank session_id means
        that the orchestrator should create a new session.

        Args:
            request: Chat request to validate.

        Raises:
            ValidationException:
                If the message is empty or whitespace-only.
        """

        # ── Validate message ─────────────────────────

        query = request.message

        if not isinstance(query, str) or not query.strip():
            raise ValidationException(
                message="Query must not be empty or whitespace-only.",
                details={
                    "field": "message",
                    "value": repr(query),
                },
            )

        # ── Validate session ID if supplied ──────────

        session_id = request.session_id

        if session_id is not None and not isinstance(session_id, str):
            raise ValidationException(
                message="Session ID must be a string when provided.",
                details={
                    "field": "session_id",
                    "value": repr(session_id),
                },
            )

        logger.info(
            "Request validation passed",
            extra={
                "query_length": len(query.strip()),
                "has_session_id": bool(
                    session_id and session_id.strip()
                ),
            },
        )

    def _execute_chat(self, request: ChatRequest) -> ChatResponse:
        """Delegate chat execution to the RAG orchestrator.

        IMPORTANT:
        A missing session_id is passed as None rather than "".

        This allows RAGOrchestrator._validate() and _ensure_session()
        to correctly recognize that this is a new conversation.

        If a session_id exists, it is passed unchanged so conversation
        memory can be preserved.

        Args:
            request: Validated chat request.

        Returns:
            ChatResponse returned by the orchestrator.
        """

        logger.info(
            "Delegating request to RAG orchestrator",
            extra={
                "has_session_id": bool(
                    request.session_id
                    and request.session_id.strip()
                ),
            },
        )

        # Do NOT use:
        #
        #     request.session_id or ""
        #
        # because "" is later interpreted as an explicitly supplied
        # session ID and can trigger validation errors.
        #
        # Instead, use None when no session ID was supplied.

        session_id = (
            request.session_id.strip()
            if request.session_id
            and request.session_id.strip()
            else None
        )

        response = self._orchestrator.chat(
            session_id=session_id,
            query=request.message.strip(),
        )

        logger.info(
            "RAG orchestrator returned response",
            extra={
                "session_id": response.session_id,
                "source_count": len(response.sources),
            },
        )

        return response

    def _build_health_response(self) -> dict[str, Any]:
        """Build the service health check response.

        Returns:
            Dictionary containing status, service name, timestamp,
            and version.
        """

        return {
            "status": "healthy",
            "service": "chat",
            "timestamp": datetime.now(UTC).isoformat(),
            "version": _SERVICE_VERSION,
        }